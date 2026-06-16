"""
Construit une configuration de dashboard (widgets) à partir des tweets analysés
en base, pour les cibles données. Compatible avec GeneratedDashboardRenderer côté
frontend (sentiment_distribution, insight_summary, target_comparison,
sentiment_timeline, keyword_topics).

Utilisé pour que les dashboards générés par le RAG affichent de vrais graphiques,
pas seulement la synthèse texte.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.target import Target
from backend.app.models.tweet import Tweet

POSITIVE = {"joie", "amour"}
NEGATIVE = {"colere", "tristesse", "peur"}

_STOP = set("""
le la les un une des de du au aux et ou mais donc car que qui quoi ce cette ces
je tu il elle on nous vous ils elles ne pas plus pour par avec sans sur dans est
sont the a an of to in on for and or but is are was be been has have this that it
he she they we you my your not no yes so just like get rt http https com www amp co
avec tout tous toutes avoir etre faire fait cette cet ces leur leurs notre votre
tweet tweets twitter via peut peux tres trop quand comme nous vous dans pour plus
moins apres avant encore ici bien rien tout monde aujourd hui demain hier depuis
""".split())


def _tokenize(text: str, excluded_terms: set[str] | None = None) -> list[str]:
    excluded_terms = excluded_terms or set()
    text = (text or "").lower()
    text = re.sub(r"http\S+", " ", text)
    raw_terms = re.findall(r"#?[a-z0-9_àâçéèêëîïôûùüÿñæœ]{3,}", text)
    terms = []
    for raw in raw_terms:
        term = raw.strip("#")
        if not term or term in _STOP or term in excluded_terms or term.isdigit():
            continue
        terms.append(term)
    return terms


def _keyword_score(count: int, doc_count: int, sentiment_counts: Counter) -> float:
    # Favorise les mots fréquents, présents dans plusieurs tweets, et émotionnellement marqués.
    total = sum(sentiment_counts.values()) or 1
    pos = sum(sentiment_counts.get(s, 0) for s in POSITIVE)
    neg = sum(sentiment_counts.get(s, 0) for s in NEGATIVE)
    emotional_weight = 1 + abs(pos - neg) / total
    spread_weight = 1 + min(doc_count, 8) / 16
    return round(count * emotional_weight * spread_weight, 3)


def extract_relevant_keywords(tweets: list[Tweet], target_name: str | None = None, limit: int = 16) -> list[dict[str, Any]]:
    excluded = set()
    if target_name:
        excluded.add(str(target_name).lower().lstrip("#@"))

    counts: Counter[str] = Counter()
    docs: Counter[str] = Counter()
    sentiment_by_term: dict[str, Counter] = defaultdict(Counter)

    for tweet in tweets:
        terms = _tokenize(tweet.text or "", excluded)
        if not terms:
            continue
        counts.update(terms)
        docs.update(set(terms))
        sentiment = tweet.sentiment or "neutre"
        for term in set(terms):
            sentiment_by_term[term][sentiment] += 1

    rows = []
    for term, count in counts.items():
        if count <= 1 and len(counts) > 5:
            continue
        sentiment_counts = sentiment_by_term[term]
        dominant = sentiment_counts.most_common(1)[0][0] if sentiment_counts else None
        rows.append({
            "term": term,
            "count": count,
            "doc_count": docs[term],
            "score": _keyword_score(count, docs[term], sentiment_counts),
            "dominant_sentiment": dominant,
            "sentiment_counts": dict(sentiment_counts),
        })

    rows.sort(key=lambda item: (item["score"], item["doc_count"], item["count"]), reverse=True)
    return rows[:limit]


def _net_label(net: float) -> str:
    if net >= 0.4:
        return "Tonalité très positive"
    if net >= 0.1:
        return "Tonalité plutôt positive"
    if net > -0.1:
        return "Tonalité partagée"
    if net > -0.4:
        return "Tonalité plutôt négative"
    return "Tonalité très négative"


def build_dashboard_config(db: Session, target_ids: list[int], question: str | None = None) -> dict[str, Any]:
    """Retourne un config_json avec widgets, ou un dict minimal si pas de données."""
    if not target_ids:
        return {"source_question": question, "target_ids": [], "widgets": [], "generated_at": datetime.utcnow().isoformat()}

    targets = db.query(Target).filter(Target.id.in_(target_ids)).all()

    distribution_data = []
    insight_data = []
    comparison_data = []
    keyword_data = []
    timeline_data: dict[str, list] = {}

    for tgt in targets:
        tws = (
            db.query(Tweet)
            .filter(Tweet.target_id == tgt.id, Tweet.sentiment.isnot(None))
            .all()
        )
        if not tws:
            continue

        counts = Counter(t.sentiment for t in tws)
        total = sum(counts.values())
        distribution = {s: round(c / total, 4) for s, c in counts.items()}
        pos = sum(counts.get(s, 0) for s in POSITIVE)
        neg = sum(counts.get(s, 0) for s in NEGATIVE)
        net = round((pos - neg) / total, 4) if total else 0
        confs = [float(t.confidence) for t in tws if t.confidence is not None]
        avg_conf = round(sum(confs) / len(confs), 4) if confs else 0
        dominant = counts.most_common(1)[0][0] if counts else "neutre"

        distribution_data.append({
            "target_id": tgt.id,
            "target_name": tgt.name,
            "counts": dict(counts),
            "distribution": distribution,
        })
        insight_data.append({
            "target_id": tgt.id,
            "target_name": tgt.name,
            "net_sentiment_score": net,
            "net_sentiment_label": _net_label(net),
            "positive_ratio": round(pos / total, 4) if total else 0,
            "negative_ratio": round(neg / total, 4) if total else 0,
            "average_confidence": avg_conf,
        })
        comparison_data.append({
            "target_name": tgt.name,
            "sentiment_distribution": distribution,
            "total_tweets": total,
            "dominant_sentiment": dominant,
            "net_sentiment_score": net,
        })

        keyword_data.append({
            "target_id": tgt.id,
            "target_name": tgt.name,
            "keywords": extract_relevant_keywords(tws, target_name=tgt.name, limit=16),
        })

        # Timeline par jour
        by_day: dict[str, Counter] = defaultdict(Counter)
        for t in tws:
            dt = t.analyzed_at or t.tweet_created_at
            day = dt.strftime("%Y-%m-%d") if dt else datetime.utcnow().strftime("%Y-%m-%d")
            by_day[day][t.sentiment] += 1
        series = []
        for day in sorted(by_day.keys()):
            c = by_day[day]
            d_total = sum(c.values())
            d_pos = sum(c.get(s, 0) for s in POSITIVE)
            d_neg = sum(c.get(s, 0) for s in NEGATIVE)
            series.append({"date": day, "net_sentiment_score": round((d_pos - d_neg) / d_total, 4) if d_total else 0})
        timeline_data[tgt.name] = series

    widgets = []
    if distribution_data:
        widgets.append({"type": "insight_summary", "title": "Lecture rapide", "data": insight_data})
        widgets.append({"type": "sentiment_distribution", "title": "Répartition des sentiments", "data": distribution_data})
        if len(comparison_data) >= 2:
            widgets.append({"type": "target_comparison", "title": "Comparaison des cibles", "data": comparison_data})
        widgets.append({"type": "sentiment_timeline", "title": "Évolution temporelle", "data": timeline_data})
        widgets.append({"type": "keyword_topics", "title": "Mots récurrents", "data": keyword_data})

    return {
        "source_question": question,
        "target_ids": target_ids,
        "widgets": widgets,
        "generated_at": datetime.utcnow().isoformat(),
    }
