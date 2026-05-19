import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.target import Target
from backend.app.models.tweet import Tweet, VALID_SENTIMENTS


def normalize_text(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text


def tokenize(text: str):
    text = normalize_text(text)
    return re.findall(r"[a-z0-9_#@]+", text)


class TinyIntentModel:
    """
    Mini modèle NLP entraîné from scratch.
    Il sert à comprendre l'intention de la question :
    - résumé global
    - comparaison
    - évolution temporelle
    - génération dashboard
    - exemples de tweets
    """

    def __init__(self):
        self.intent_word_counts = defaultdict(Counter)
        self.intent_counts = Counter()
        self.vocab = set()
        self.total_examples = 0

    def fit(self, examples):
        for text, intent in examples:
            tokens = tokenize(text)
            self.intent_counts[intent] += 1
            self.total_examples += 1

            for token in tokens:
                self.intent_word_counts[intent][token] += 1
                self.vocab.add(token)

    def predict(self, question: str):
        tokens = tokenize(question)

        if not tokens:
            return "summary", 0.0

        best_intent = None
        best_score = -10**9
        scores = {}

        vocab_size = max(len(self.vocab), 1)

        for intent in self.intent_counts:
            prior = math.log(self.intent_counts[intent] / self.total_examples)
            total_words = sum(self.intent_word_counts[intent].values())

            score = prior
            for token in tokens:
                count = self.intent_word_counts[intent][token]
                proba = (count + 1) / (total_words + vocab_size)
                score += math.log(proba)

            scores[intent] = score

            if score > best_score:
                best_score = score
                best_intent = intent

        sorted_scores = sorted(scores.values(), reverse=True)

        if len(sorted_scores) >= 2:
            confidence = min(1.0, max(0.0, sorted_scores[0] - sorted_scores[1]))
        else:
            confidence = 1.0

        return best_intent or "summary", round(confidence, 3)


TRAINING_EXAMPLES = [
    ("résume l'activité de ce compte", "summary"),
    ("quel est le sentiment dominant", "summary"),
    ("comment les gens réagissent", "summary"),
    ("donne moi une synthèse", "summary"),
    ("résumé des sentiments", "summary"),

    ("compare ces hashtags", "comparison"),
    ("comparaison entre ces comptes", "comparison"),
    ("lequel est le plus positif", "comparison"),
    ("qui a le plus de colère", "comparison"),
    ("compare les sentiments", "comparison"),

    ("évolution temporelle des sentiments", "timeline"),
    ("comment ça évolue dans le temps", "timeline"),
    ("tendance sur les derniers jours", "timeline"),
    ("est-ce que la joie augmente", "timeline"),
    ("analyse temporelle", "timeline"),

    ("génère un dashboard", "dashboard"),
    ("fais moi un dashboard", "dashboard"),
    ("je veux des graphiques", "dashboard"),
    ("prépare une visualisation", "dashboard"),

    ("montre des exemples de tweets négatifs", "examples"),
    ("donne des tweets représentatifs", "examples"),
    ("exemples de tweets joyeux", "examples"),
    ("tweets les plus tristes", "examples"),

    
]

INTENT_MODEL = TinyIntentModel()
INTENT_MODEL.fit(TRAINING_EXAMPLES)


def extract_days(question: str, default_days: int = 7) -> int:
    q = normalize_text(question)

    match = re.search(r"(\d+)\s*(jour|jours|j|day|days)", q)
    if match:
        return max(1, min(90, int(match.group(1))))

    if "semaine" in q:
        return 7

    if "mois" in q:
        return 30

    return default_days


def detect_sentiment_filter(question: str):
    q = normalize_text(question)

    aliases = {
        "joie": ["joie", "joyeux", "positif", "positive", "heureux"],
        "tristesse": ["tristesse", "triste", "negatif", "negative"],
        "colere": ["colere", "colère", "rage", "enerve", "énervé"],
        "peur": ["peur", "inquiet", "inquiétude", "anxiete"],
        "surprise": ["surprise", "etonne", "étonné"],
        "neutre": ["neutre", "neutral"],
        "amour": ["amour", "love"],
    }

    for sentiment, words in aliases.items():
        if any(word in q for word in words):
            return sentiment

    return None


def get_user_targets(db: Session, user_id: int, target_ids: list[int]):
    targets = (
        db.query(Target)
        .filter(Target.user_id == user_id, Target.id.in_(target_ids))
        .all()
    )

    found_ids = {target.id for target in targets}
    missing_ids = [target_id for target_id in target_ids if target_id not in found_ids]

    if missing_ids:
        raise ValueError(f"Cibles introuvables ou non autorisées : {missing_ids}")

    return targets


def compute_target_stats(db: Session, target: Target, since: datetime):
    base_query = (
        db.query(Tweet)
        .filter(
            Tweet.target_id == target.id,
            Tweet.sentiment.isnot(None),
            Tweet.analyzed_at >= since,
        )
    )

    total = base_query.count()

    rows = (
        db.query(
            Tweet.sentiment,
            func.count(Tweet.id).label("count"),
            func.avg(Tweet.confidence).label("avg_confidence"),
        )
        .filter(
            Tweet.target_id == target.id,
            Tweet.sentiment.isnot(None),
            Tweet.analyzed_at >= since,
        )
        .group_by(Tweet.sentiment)
        .all()
    )

    sentiment_counts = {sentiment: 0 for sentiment in VALID_SENTIMENTS}
    sentiment_counts["neutre"] = 0

    confidence_by_sentiment = {}

    for row in rows:
        sentiment_counts[row.sentiment] = int(row.count)
        confidence_by_sentiment[row.sentiment] = round(float(row.avg_confidence or 0), 3)

    if total > 0:
        sentiment_distribution = {
            sentiment: round(count / total, 3)
            for sentiment, count in sentiment_counts.items()
        }
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
    else:
        sentiment_distribution = {
            sentiment: 0.0
            for sentiment in sentiment_counts
        }
        dominant_sentiment = None

    avg_confidence = (
        db.query(func.avg(Tweet.confidence))
        .filter(
            Tweet.target_id == target.id,
            Tweet.sentiment.isnot(None),
            Tweet.analyzed_at >= since,
        )
        .scalar()
    )

    return {
        "target_id": target.id,
        "target_name": target.name,
        "target_type": str(target.target_type.value if hasattr(target.target_type, "value") else target.target_type),
        "total_tweets": total,
        "dominant_sentiment": dominant_sentiment,
        "sentiment_counts": sentiment_counts,
        "sentiment_distribution": sentiment_distribution,
        "average_confidence": round(float(avg_confidence or 0), 3),
    }


def compute_timeline(db: Session, target: Target, since: datetime):
    day_expr = func.date(Tweet.analyzed_at)

    rows = (
        db.query(
            day_expr.label("day"),
            Tweet.sentiment,
            func.count(Tweet.id).label("count"),
        )
        .filter(
            Tweet.target_id == target.id,
            Tweet.sentiment.isnot(None),
            Tweet.analyzed_at >= since,
        )
        .group_by(day_expr, Tweet.sentiment)
        .order_by(day_expr)
        .all()
    )

    timeline = {}

    for row in rows:
        day = str(row.day)
        if day not in timeline:
            timeline[day] = {
                "date": day,
                "target_id": target.id,
                "target_name": target.name,
                "total": 0,
                "sentiments": defaultdict(int),
            }

        timeline[day]["sentiments"][row.sentiment] += int(row.count)
        timeline[day]["total"] += int(row.count)

    result = []
    for item in timeline.values():
        item["sentiments"] = dict(item["sentiments"])
        result.append(item)

    return result


def get_representative_tweets(
    db: Session,
    target_ids: list[int],
    since: datetime,
    sentiment_filter: str | None = None,
    limit: int = 5,
):
    query = (
        db.query(Tweet)
        .filter(
            Tweet.target_id.in_(target_ids),
            Tweet.sentiment.isnot(None),
            Tweet.analyzed_at >= since,
        )
    )

    if sentiment_filter:
        query = query.filter(Tweet.sentiment == sentiment_filter)

    tweets = (
        query
        .order_by(Tweet.confidence.desc().nullslast())
        .limit(limit)
        .all()
    )

    return [
        {
            "tweet_id": tweet.id,
            "author": tweet.author_username,
            "text": tweet.text,
            "sentiment": tweet.sentiment,
            "confidence": round(float(tweet.confidence or 0), 3),
            "created_at": str(tweet.tweet_created_at) if tweet.tweet_created_at else None,
        }
        for tweet in tweets
    ]


def generate_text_answer(intent: str, stats: list[dict], timeline: list[dict], examples: list[dict]):
    if not stats:
        return "Je n'ai trouvé aucune cible à analyser."

    total_tweets = sum(item["total_tweets"] for item in stats)

    if total_tweets == 0:
        return (
            "Je n'ai pas encore assez de tweets analysés pour répondre. "
            "Lance d'abord une collecte puis une analyse de sentiment sur les cibles sélectionnées."
        )

    if intent == "comparison":
        sorted_stats = sorted(stats, key=lambda x: x["total_tweets"], reverse=True)

        lines = ["Comparaison des cibles sélectionnées :"]

        for item in sorted_stats:
            dominant = item["dominant_sentiment"] or "inconnu"
            percent = item["sentiment_distribution"].get(dominant, 0) if dominant != "inconnu" else 0
            lines.append(
                f"- {item['target_name']} : {item['total_tweets']} tweets analysés, "
                f"sentiment dominant = {dominant} ({percent:.0%})."
            )

        most_positive = max(
            stats,
            key=lambda x: x["sentiment_distribution"].get("joie", 0)
        )

        lines.append(
            f"La cible la plus positive semble être {most_positive['target_name']} "
            f"avec {most_positive['sentiment_distribution'].get('joie', 0):.0%} de joie."
        )

        return "\n".join(lines)

    if intent == "timeline":
        if not timeline:
            return "Je n'ai pas assez de données temporelles pour produire une tendance fiable."

        return (
            f"J'ai trouvé {total_tweets} tweets analysés sur la période. "
            "La tendance temporelle est disponible dans le dashboard généré. "
            "Tu peux l'utiliser pour visualiser l'évolution des sentiments jour par jour."
        )

    if intent == "examples":
        if not examples:
            return "Je n'ai pas trouvé de tweets représentatifs pour cette demande."

        lines = ["Voici quelques tweets représentatifs :"]
        for tweet in examples:
            lines.append(
                f"- @{tweet['author'] or '?'} : \"{tweet['text'][:140]}\" "
                f"→ {tweet['sentiment']} ({tweet['confidence']:.0%})"
            )

        return "\n".join(lines)

    lines = [f"Synthèse globale sur {total_tweets} tweets analysés :"]

    for item in stats:
        dominant = item["dominant_sentiment"] or "inconnu"
        percent = item["sentiment_distribution"].get(dominant, 0) if dominant != "inconnu" else 0
        lines.append(
            f"- {item['target_name']} : sentiment dominant = {dominant} "
            f"({percent:.0%}), confiance moyenne = {item['average_confidence']:.0%}."
        )

    return "\n".join(lines)


def generate_dashboard_config(question: str, intent: str, stats: list[dict], timeline_by_target: dict):
    widgets = []

    widgets.append({
        "type": "sentiment_distribution",
        "title": "Répartition des sentiments",
        "chart": "pie",
        "data": [
            {
                "target_id": item["target_id"],
                "target_name": item["target_name"],
                "distribution": item["sentiment_distribution"],
                "counts": item["sentiment_counts"],
            }
            for item in stats
        ],
    })

    if len(stats) > 1 or intent == "comparison":
        widgets.append({
            "type": "target_comparison",
            "title": "Comparaison des cibles",
            "chart": "bar",
            "data": [
                {
                    "target_id": item["target_id"],
                    "target_name": item["target_name"],
                    "total_tweets": item["total_tweets"],
                    "dominant_sentiment": item["dominant_sentiment"],
                    "sentiment_distribution": item["sentiment_distribution"],
                }
                for item in stats
            ],
        })

    if intent in ["timeline", "dashboard", "summary", "comparison"]:
        widgets.append({
            "type": "sentiment_timeline",
            "title": "Évolution temporelle des sentiments",
            "chart": "line",
            "data": timeline_by_target,
        })

    return {
        "title": "Dashboard généré par le LLM SentiFlow",
        "source_question": question,
        "intent": intent,
        "generated_at": datetime.utcnow().isoformat(),
        "widgets": widgets,
    }


def ask_local_llm(
    db: Session,
    user_id: int,
    question: str,
    target_ids: list[int],
    days: int = 7,
    generate_dashboard: bool = True,
):
    if not target_ids:
        raise ValueError("Il faut sélectionner au moins une cible.")

    detected_days = extract_days(question, default_days=days)
    since = datetime.utcnow() - timedelta(days=detected_days)

    intent, intent_confidence = INTENT_MODEL.predict(question)
    sentiment_filter = detect_sentiment_filter(question)

    targets = get_user_targets(db, user_id, target_ids)

    stats = [
        compute_target_stats(db, target, since)
        for target in targets
    ]

    timeline_by_target = {
        target.name: compute_timeline(db, target, since)
        for target in targets
    }

    all_timeline_rows = []
    for rows in timeline_by_target.values():
        all_timeline_rows.extend(rows)

    examples = get_representative_tweets(
        db=db,
        target_ids=target_ids,
        since=since,
        sentiment_filter=sentiment_filter,
        limit=5,
    )

    answer = generate_text_answer(
        intent=intent,
        stats=stats,
        timeline=all_timeline_rows,
        examples=examples,
    )

    dashboard_config = None
    if generate_dashboard or intent == "dashboard":
        dashboard_config = generate_dashboard_config(
            question=question,
            intent=intent,
            stats=stats,
            timeline_by_target=timeline_by_target,
        )

    return {
        "question": question,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "period_days": detected_days,
        "sentiment_filter": sentiment_filter,
        "answer": answer,
        "targets": stats,
        "examples": examples,
        "dashboard_config": dashboard_config,
    }