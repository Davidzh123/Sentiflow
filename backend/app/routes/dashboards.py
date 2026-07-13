from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.generated_dashboard import GeneratedDashboard
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet
from backend.app.models.user import User
from backend.app.services.auth import get_current_user


router = APIRouter(prefix="/dashboards", tags=["Dashboards générés"])

POSITIVE = {"joie", "amour"}
NEGATIVE = {"colere", "tristesse", "peur"}


def _dashboard_period(dashboard: GeneratedDashboard) -> tuple[datetime | None, datetime]:
    """Retourne la période réellement associée au plan du dashboard."""
    end = dashboard.created_at or datetime.utcnow()
    plan = dashboard.plan_json or {}
    try:
        days = int(plan.get("days") or 0)
    except (TypeError, ValueError):
        days = 0
    days = max(0, min(days, 365))
    start = end - timedelta(days=days) if days else None
    return start, end


def _tweet_date(tweet: Tweet) -> datetime | None:
    return tweet.tweet_created_at or getattr(tweet, "collected_at", None) or tweet.analyzed_at


def _representative_tweets(tweets: list[Tweet], limit: int = 4) -> list[Tweet]:
    """Diversifie les exemples : un tweet fort par sentiment, puis complète par confiance."""
    ordered = sorted(tweets, key=lambda item: float(item.confidence or 0), reverse=True)
    selected: list[Tweet] = []
    seen_sentiments: set[str] = set()
    for tweet in ordered:
        sentiment = str(tweet.sentiment or "inconnu")
        if sentiment in seen_sentiments:
            continue
        selected.append(tweet)
        seen_sentiments.add(sentiment)
        if len(selected) >= limit:
            return selected
    for tweet in ordered:
        if tweet not in selected:
            selected.append(tweet)
        if len(selected) >= limit:
            break
    return selected


class GeneratedDashboardCreate(BaseModel):
    title: str = Field(default="Dashboard généré", max_length=255)
    question: str = Field(..., min_length=1)
    answer: str | None = None
    target_ids: list[int] = Field(default_factory=list)
    config_json: dict[str, Any]
    plan_json: dict[str, Any] | None = None


def serialize_dashboard(dashboard: GeneratedDashboard, include_config: bool = True) -> dict[str, Any]:
    data = {
        "id": dashboard.id,
        "title": dashboard.title,
        "question": dashboard.question,
        "answer": dashboard.answer,
        "target_ids": dashboard.target_ids or [],
        "created_at": dashboard.created_at.isoformat() if dashboard.created_at else None,
        "updated_at": dashboard.updated_at.isoformat() if dashboard.updated_at else None,
    }

    if include_config:
        data["config_json"] = dashboard.config_json
        data["dashboard_config"] = dashboard.config_json
        data["plan_json"] = dashboard.plan_json

    return data


def _serialize_tweet(tweet: Tweet, target_by_id: dict[int, Target]) -> dict[str, Any]:
    target = target_by_id.get(tweet.target_id)
    display_date = tweet.tweet_created_at or getattr(tweet, "collected_at", None) or tweet.analyzed_at
    collected_at = getattr(tweet, "collected_at", None) or tweet.analyzed_at

    return {
        "tweet_id": tweet.id,
        "twitter_id": tweet.twitter_id,
        "target_id": tweet.target_id,
        "target_name": target.name if target else None,
        "target_type": (
            str(target.target_type.value if hasattr(target.target_type, "value") else target.target_type)
            if target
            else None
        ),
        "author": tweet.author_username,
        "text": tweet.text,
        "sentiment": tweet.sentiment,
        "confidence": round(float(tweet.confidence or 0), 3),
        "tweet_created_at": tweet.tweet_created_at.isoformat() if tweet.tweet_created_at else None,
        "collected_at": collected_at.isoformat() if collected_at else None,
        "analyzed_at": tweet.analyzed_at.isoformat() if tweet.analyzed_at else None,
        "display_date": display_date.isoformat() if display_date else None,
    }


@router.get("/")
def list_generated_dashboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboards = (
        db.query(GeneratedDashboard)
        .filter(GeneratedDashboard.user_id == current_user.id)
        .order_by(GeneratedDashboard.created_at.desc())
        .all()
    )

    return [serialize_dashboard(dashboard, include_config=False) for dashboard in dashboards]


@router.get("/{dashboard_id}")
def get_generated_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admin peut voir tous les dashboards
    if current_user.is_admin:
        dashboard = db.query(GeneratedDashboard).filter(
            GeneratedDashboard.id == dashboard_id
        ).first()
    else:
        dashboard = db.query(GeneratedDashboard).filter(
            GeneratedDashboard.id == dashboard_id,
            GeneratedDashboard.user_id == current_user.id,
        ).first()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard introuvable")

    return serialize_dashboard(dashboard, include_config=True)


@router.get("/{dashboard_id}/tweets")
def get_dashboard_tweets(
    dashboard_id: int,
    q: str | None = Query(default=None, max_length=200),
    sentiment: str | None = Query(default=None, max_length=30),
    target_id: int | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=3000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_admin:
        dashboard = db.query(GeneratedDashboard).filter(
            GeneratedDashboard.id == dashboard_id
        ).first()
    else:
        dashboard = db.query(GeneratedDashboard).filter(
            GeneratedDashboard.id == dashboard_id,
            GeneratedDashboard.user_id == current_user.id,
        ).first()

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard introuvable")

    target_ids = [int(value) for value in (dashboard.target_ids or []) if value is not None]
    if not target_ids:
        return {"total": 0, "returned": 0, "tweets": []}

    targets = db.query(Target).filter(Target.id.in_(target_ids)).all()
    target_by_id = {target.id: target for target in targets}

    query = db.query(Tweet).filter(
        Tweet.target_id.in_(target_ids),
        Tweet.sentiment.isnot(None),
    )
    if sentiment:
        query = query.filter(Tweet.sentiment == sentiment)
    if target_id:
        query = query.filter(Tweet.target_id == target_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(Tweet.text.ilike(pattern))

    tweets = query.all()
    tweets.sort(
        key=lambda tweet: tweet.tweet_created_at or getattr(tweet, "collected_at", None) or tweet.analyzed_at or datetime.min,
        reverse=True,
    )
    rows = [_serialize_tweet(tweet, target_by_id) for tweet in tweets[:limit]]

    return {
        "total": len(tweets),
        "returned": len(rows),
        "tweets": rows,
    }


@router.post("/")
def create_generated_dashboard(
    payload: GeneratedDashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = GeneratedDashboard(
        user_id=current_user.id,
        title=payload.title or "Dashboard généré",
        question=payload.question,
        answer=payload.answer,
        target_ids=payload.target_ids,
        config_json=payload.config_json,
        plan_json=payload.plan_json,
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)

    return serialize_dashboard(dashboard, include_config=True)


@router.get("/{dashboard_id}/pdf")
def export_dashboard_pdf(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exporte un rapport analytique complet et cohérent avec la période du dashboard.

    Contrairement à l'ancienne version, l'export ne mélange plus automatiquement
    tous les tweets historiques d'une cible avec une requête portant sur quelques jours.
    """
    if current_user.is_admin:
        dashboard = db.query(GeneratedDashboard).filter(GeneratedDashboard.id == dashboard_id).first()
    else:
        dashboard = db.query(GeneratedDashboard).filter(
            GeneratedDashboard.id == dashboard_id,
            GeneratedDashboard.user_id == current_user.id,
        ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard introuvable")

    target_ids = [int(value) for value in (dashboard.target_ids or []) if value is not None]
    period_start, period_end = _dashboard_period(dashboard)
    targets_data: list[dict[str, Any]] = []
    representative: list[dict[str, Any]] = []

    if target_ids:
        from backend.app.services.dashboard_builder import extract_relevant_keywords

        targets = db.query(Target).filter(Target.id.in_(target_ids)).all()
        date_expr = func.coalesce(Tweet.tweet_created_at, Tweet.collected_at, Tweet.analyzed_at)

        for target in targets:
            query = db.query(Tweet).filter(
                Tweet.target_id == target.id,
                Tweet.sentiment.isnot(None),
            )
            if period_start is not None:
                # Petite marge après la création pour absorber un commit exécuté au même instant.
                query = query.filter(
                    date_expr >= period_start,
                    date_expr <= period_end + timedelta(minutes=5),
                )
            tweets = query.all()
            if not tweets:
                continue

            counts = Counter(str(tweet.sentiment or "inconnu") for tweet in tweets)
            total = sum(counts.values())
            distribution = {sentiment: count / total for sentiment, count in counts.items()}
            positive = sum(counts.get(sentiment, 0) for sentiment in POSITIVE)
            negative = sum(counts.get(sentiment, 0) for sentiment in NEGATIVE)
            confidences = [float(tweet.confidence) for tweet in tweets if tweet.confidence is not None]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0
            net_score = (positive - negative) / total if total else 0

            by_day: dict[str, Counter] = defaultdict(Counter)
            for tweet in tweets:
                date = _tweet_date(tweet)
                if not date:
                    continue
                by_day[date.strftime("%Y-%m-%d")][str(tweet.sentiment or "inconnu")] += 1
            timeline = []
            for day in sorted(by_day):
                day_counts = by_day[day]
                day_total = sum(day_counts.values())
                day_positive = sum(day_counts.get(sentiment, 0) for sentiment in POSITIVE)
                day_negative = sum(day_counts.get(sentiment, 0) for sentiment in NEGATIVE)
                timeline.append({
                    "date": day,
                    "net_sentiment_score": (day_positive - day_negative) / day_total if day_total else 0,
                })

            targets_data.append({
                "name": target.name,
                "total": total,
                "distribution": distribution,
                "positive": positive,
                "negative": negative,
                "dominant_sentiment": counts.most_common(1)[0][0] if counts else "inconnu",
                "average_confidence": average_confidence,
                "net_sentiment_score": net_score,
                "timeline": timeline,
                "keywords": extract_relevant_keywords(tweets, target_name=target.name, limit=12),
            })

            for tweet in _representative_tweets(tweets, limit=4):
                representative.append({
                    "author": tweet.author_username or "?",
                    "sentiment": tweet.sentiment or "inconnu",
                    "confidence": float(tweet.confidence or 0),
                    "text": tweet.text or "",
                    "target": target.name,
                    "date": _tweet_date(tweet).isoformat() if _tweet_date(tweet) else None,
                })

    representative.sort(key=lambda item: float(item.get("confidence", 0)), reverse=True)

    collection_note = None
    if period_start is not None and not targets_data:
        collection_note = (
            "Aucun tweet analysé n'a été trouvé dans la période demandée. "
            "Le rapport n'inclut pas les anciens tweets afin de ne pas fausser les résultats."
        )

    from backend.app.services.pdf_generator import generate_report_pdf

    pdf_bytes = generate_report_pdf(
        title=dashboard.title or "Dashboard IA",
        question=dashboard.question or "",
        created_at=str(dashboard.created_at) if dashboard.created_at else None,
        targets=targets_data,
        tweets=representative,
        synthesis=dashboard.answer,
        period_start=period_start,
        period_end=period_end,
        collection_note=collection_note,
    )
    if pdf_bytes is None:
        raise HTTPException(status_code=500, detail="Generation PDF indisponible (fpdf2 non installe)")

    from backend.app.services.notifications import notify

    notify(
        db,
        current_user.id,
        "pdf_export",
        "Export PDF",
        f"Le rapport « {dashboard.title} » a été exporté en PDF.",
    )

    filename = f"rapport_dashboard_{dashboard.id}.pdf"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/{dashboard_id}")
def delete_generated_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dashboard = (
        db.query(GeneratedDashboard)
        .filter(
            GeneratedDashboard.id == dashboard_id,
            GeneratedDashboard.user_id == current_user.id,
        )
        .first()
    )

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard introuvable")

    db.delete(dashboard)
    db.commit()

    return {"message": "Dashboard supprimé"}
