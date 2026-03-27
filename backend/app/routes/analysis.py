from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import sys

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.tweet import Tweet, VALID_SENTIMENTS
from backend.app.models.target import Target
from backend.app.schemas.tweet import SentimentAnalysis
from backend.app.services.auth import get_current_user

# Ajouter le path pour importer le modèle sentiment
sys.path.insert(0, ".")
from services.sentiment.model import get_analyzer

router = APIRouter(prefix="/analysis", tags=["Analyse"])


@router.post("/{target_id}/analyze")
def analyze_tweets(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyse les tweets non analysés d'une cible avec le modèle de sentiment"""
    
    # Vérifier que la cible appartient à l'utilisateur
    target = db.query(Target).filter(
        Target.id == target_id, 
        Target.user_id == current_user.id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    # Récupérer les tweets non analysés
    tweets = db.query(Tweet).filter(
        Tweet.target_id == target_id,
        Tweet.sentiment.is_(None)
    ).all()
    
    if not tweets:
        return {"message": "Aucun tweet à analyser", "analyzed": 0}
    
    # Charger le modèle
    analyzer = get_analyzer()
    
    analyzed_count = 0
    
    for tweet in tweets:
        try:
            # Prédire le sentiment
            scores = analyzer.predict(tweet.text)
            dominant, confidence = analyzer.get_dominant_sentiment(scores)
            
            # Mettre à jour le tweet
            tweet.sentiment_scores = scores
            tweet.confidence = confidence
            tweet.sentiment = dominant  # "joie", "colere", etc. en minuscules
            tweet.analyzed_at = datetime.utcnow()
            
            analyzed_count += 1
        except Exception as e:
            print(f"Erreur analyse tweet {tweet.id}: {e}")
            continue
    
    db.commit()
    
    return {
        "message": f"{analyzed_count} tweets analysés",
        "analyzed": analyzed_count,
        "total": len(tweets)
    }


@router.get("/{target_id}", response_model=SentimentAnalysis)
def get_sentiment_analysis(
    target_id: int,
    days: int = Query(default=7, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère l'analyse de sentiment pour une cible"""
    
    # Vérifier que la cible appartient à l'utilisateur
    target = db.query(Target).filter(
        Target.id == target_id, 
        Target.user_id == current_user.id
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Compter les tweets par sentiment
    results = db.query(
        Tweet.sentiment,
        func.count(Tweet.id).label("count"),
        func.avg(Tweet.confidence).label("avg_confidence")
    ).filter(
        Tweet.target_id == target_id,
        Tweet.analyzed_at >= since,
        Tweet.sentiment.isnot(None)
    ).group_by(Tweet.sentiment).all()
    
    total = sum(r.count for r in results)
    
    # Construire la distribution
    distribution = {s: 0.0 for s in VALID_SENTIMENTS}
    avg_confidence = 0.0
    
    if total > 0:
        for r in results:
            if r.sentiment in distribution:
                distribution[r.sentiment] = round(r.count / total, 3)
        avg_confidence = sum(r.avg_confidence * r.count for r in results) / total
    
    return SentimentAnalysis(
        target_id=target_id,
        target_name=target.name,
        period=f"{days}d",
        total_tweets=total,
        sentiment_distribution=distribution,
        average_confidence=round(avg_confidence, 3)
    )
