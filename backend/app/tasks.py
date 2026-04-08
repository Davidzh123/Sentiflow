import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func
from backend.app.celery_app import celery_app
from backend.app.database import SessionLocal
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet, VALID_SENTIMENTS
from backend.app.models.alert import Alert
from backend.app.models.sentiment_aggregate import SentimentAggregate


def get_db():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise


# --- COLLECTE AUTO ---

@celery_app.task(name="backend.app.tasks.collect_all_targets")
def collect_all_targets():
    """Collecte les tweets et les envoie dans Kafka"""
    from backend.app.services.twitter import twitter_service
    from backend.app.kafka_producer import get_producer, send_tweet_to_kafka, flush_producer

    db = get_db()
    try:
        targets = db.query(Target).all()

        if not targets:
            print("[Celery] Aucune cible en base, collecte ignorée")
            return {"message": "Aucune cible"}

        producer = get_producer()
        results = []

        for target in targets:
            try:
                sent = _collect_and_produce(target, twitter_service, producer)
                results.append({"target": target.name, "sent_to_kafka": sent})
            except Exception as e:
                results.append({"target": target.name, "error": str(e)})

        flush_producer(producer)
        producer.close()
        print(f"[Celery] Collecte → Kafka terminée: {results}")
        return results
    finally:
        db.close()


def _collect_and_produce(target, twitter_service, producer):
    """Collecte les tweets et les envoie dans Kafka"""
    from backend.app.kafka_producer import send_tweet_to_kafka

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if target.target_type.value == "hashtag":
            data = loop.run_until_complete(twitter_service.search_tweets(target.query))
        else:
            username = target.name.lstrip("@")
            data = loop.run_until_complete(twitter_service.get_user_tweets(username))
    finally:
        loop.close()

    if "error" in data:
        raise Exception(data["error"])

    tweets_data = data.get("tweets", data.get("data", []))
    sent = 0

    for tweet_data in tweets_data:
        if isinstance(tweet_data, dict):
            send_tweet_to_kafka(producer, tweet_data, target.id, target.name)
            sent += 1

    return sent


# --- ANALYSE AUTO ---

@celery_app.task(name="backend.app.tasks.analyze_all_targets")
def analyze_all_targets():
    """Analyse les tweets non analysés pour toutes les cibles"""
    import sys
    sys.path.insert(0, ".")
    from services.sentiment.model import get_analyzer

    db = get_db()
    try:
        analyzer = get_analyzer()

        tweets = db.query(Tweet).filter(Tweet.sentiment.is_(None)).all()

        if not tweets:
            print("[Celery] Aucun tweet à analyser")
            return {"analyzed": 0}

        analyzed = 0

        for tweet in tweets:
            try:
                scores = analyzer.predict(tweet.text)
                dominant, confidence = analyzer.get_dominant_sentiment(scores)

                tweet.sentiment_scores = scores
                tweet.confidence = confidence
                tweet.sentiment = dominant
                tweet.analyzed_at = datetime.utcnow()
                analyzed += 1
            except Exception as e:
                print(f"[Celery] Erreur analyse tweet {tweet.id}: {e}")
                continue

        db.commit()
        print(f"[Celery] Analyse terminée: {analyzed} tweets analysés")
        return {"analyzed": analyzed}
    finally:
        db.close()


# --- ALERTES AUTO ---

@celery_app.task(name="backend.app.tasks.check_all_alerts")
def check_all_alerts():
    """Vérifie toutes les alertes actives et déclenche si seuil dépassé"""
    db = get_db()
    try:
        alerts = db.query(Alert).filter(Alert.is_active == True).all()
        triggered = []

        for alert in alerts:
            try:
                was_triggered = _check_alert(db, alert)
                if was_triggered:
                    triggered.append(alert.name)
            except Exception as e:
                print(f"[Celery] Erreur alerte {alert.id}: {e}")

        db.commit()
        print(f"[Celery] Alertes vérifiées: {len(triggered)} déclenchées")
        return {"checked": len(alerts), "triggered": triggered}
    finally:
        db.close()


def _check_alert(db, alert):
    """Vérifie une alerte et la déclenche si nécessaire"""
    since = datetime.utcnow() - timedelta(days=7)

    # Compter les tweets par sentiment pour cette cible
    results = db.query(
        Tweet.sentiment,
        func.count(Tweet.id).label("count")
    ).filter(
        Tweet.target_id == alert.target_id,
        Tweet.analyzed_at >= since,
        Tweet.sentiment.isnot(None)
    ).group_by(Tweet.sentiment).all()

    total = sum(r.count for r in results)
    if total == 0:
        return False

    # Calculer le ratio du sentiment surveillé
    sentiment_count = 0
    for r in results:
        if r.sentiment == alert.sentiment:
            sentiment_count = r.count
            break

    ratio = sentiment_count / total

    # Vérifier le seuil
    if alert.is_above and ratio > alert.threshold:
        alert.last_triggered = datetime.utcnow()
        return True
    elif not alert.is_above and ratio < alert.threshold:
        alert.last_triggered = datetime.utcnow()
        return True

    return False


# --- AGRÉGATION ---

@celery_app.task(name="backend.app.tasks.aggregate_sentiments")
def aggregate_sentiments():
    """Pré-calcule les agrégations de sentiments par jour"""
    db = get_db()
    try:
        targets = db.query(Target).all()
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        for target in targets:
            # Compter les tweets du jour par sentiment
            results = db.query(
                Tweet.sentiment,
                func.count(Tweet.id).label("count")
            ).filter(
                Tweet.target_id == target.id,
                Tweet.analyzed_at >= today_start,
                Tweet.analyzed_at < today_end,
                Tweet.sentiment.isnot(None)
            ).group_by(Tweet.sentiment).all()

            total = sum(r.count for r in results)
            if total == 0:
                continue

            counts = {s: 0 for s in VALID_SENTIMENTS}
            scores = {s: 0.0 for s in VALID_SENTIMENTS}
            for r in results:
                if r.sentiment in counts:
                    counts[r.sentiment] = r.count
                    scores[r.sentiment] = round(r.count / total, 4)

            # Upsert l'agrégation du jour
            existing = db.query(SentimentAggregate).filter(
                SentimentAggregate.target_id == target.id,
                SentimentAggregate.bucket_start == today_start,
                SentimentAggregate.granularity == "day"
            ).first()

            if existing:
                existing.total_posts = total
                existing.counts_json = counts
                existing.scores_json = scores
                existing.computed_at = now
            else:
                agg = SentimentAggregate(
                    target_id=target.id,
                    bucket_start=today_start,
                    bucket_end=today_end,
                    granularity="day",
                    total_posts=total,
                    counts_json=counts,
                    scores_json=scores,
                    computed_at=now
                )
                db.add(agg)

        db.commit()
        print(f"[Celery] Agrégation terminée pour {len(targets)} cibles")
        return {"targets": len(targets)}
    finally:
        db.close()
