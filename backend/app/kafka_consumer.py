import json
import os
import sys
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

# Path pour le modèle sentiment
sys.path.insert(0, "/app")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC_TWEETS_RAW = "tweets-raw"
TOPIC_TWEETS_ANALYZED = "tweets-analyzed"


def create_consumer():
    """Crée un consumer Kafka avec retry"""
    for attempt in range(10):
        try:
            consumer = KafkaConsumer(
                TOPIC_TWEETS_RAW,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                group_id="sentiflow-analyzer",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            print(f"[Kafka Consumer] Connecté à Kafka")
            return consumer
        except NoBrokersAvailable:
            print(f"[Kafka Consumer] Kafka pas prêt, retry {attempt+1}/10...")
            time.sleep(5)

    raise Exception("Impossible de se connecter à Kafka après 10 tentatives")


def process_tweet(db, analyzer, message):
    """Traite un tweet : sauvegarde en DB + analyse sentiment"""
    from backend.app.models.tweet import Tweet

    data = message.value
    twitter_id = data.get("twitter_id", "")

    # Vérifier si le tweet existe déjà
    exists = db.query(Tweet).filter(Tweet.twitter_id == twitter_id).first()
    if exists:
        return None

    # Parser la date du tweet
    tweet_date = None
    created_at_str = data.get("created_at", "")
    if created_at_str:
        try:
            tweet_date = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
        except Exception:
            tweet_date = None

    # Analyser le sentiment
    text = data.get("text", "")
    scores = analyzer.predict(text)
    dominant, confidence = analyzer.get_dominant_sentiment(scores)

    # Sauvegarder en DB
    try:
        tweet = Tweet(
            twitter_id=twitter_id,
            target_id=data.get("target_id"),
            text=text,
            author_id=data.get("author_id", ""),
            author_username=data.get("author_username", ""),
            sentiment=dominant,
            sentiment_scores=scores,
            confidence=confidence,
            tweet_created_at=tweet_date,
            analyzed_at=datetime.utcnow(),
        )
        db.add(tweet)
        db.flush()
        db.commit()
        print(f"[Kafka Consumer] Tweet {twitter_id[:10]}... → {dominant} ({confidence:.0%})")
        return tweet
    except Exception as e:
        db.rollback()
        print(f"[Kafka Consumer] Erreur sauvegarde tweet {twitter_id[:10]}...: {e}")
        return None


def run_consumer():
    """Boucle principale du consumer"""
    from backend.app.database import SessionLocal
    from services.sentiment.model import get_analyzer

    print("[Kafka Consumer] Démarrage...")
    print("[Kafka Consumer] Chargement du modèle de sentiment...")
    analyzer = get_analyzer()
    print("[Kafka Consumer] Modèle chargé!")

    consumer = create_consumer()
    db = SessionLocal()

    print(f"[Kafka Consumer] En écoute sur le topic '{TOPIC_TWEETS_RAW}'...")
    processed = 0

    try:
        for message in consumer:
            result = process_tweet(db, analyzer, message)
            if result:
                processed += 1
                if processed % 10 == 0:
                    print(f"[Kafka Consumer] {processed} tweets traités au total")
    except KeyboardInterrupt:
        print(f"[Kafka Consumer] Arrêt. {processed} tweets traités.")
    finally:
        consumer.close()
        db.close()


if __name__ == "__main__":
    run_consumer()
