<<<<<<< HEAD
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.tweet import Tweet
from backend.app.models.target import Target
from backend.app.schemas.tweet import TweetResponse
from backend.app.services.auth import get_current_user

router = APIRouter(prefix="/tweets", tags=["Tweets"])


@router.get("/{target_id}", response_model=List[TweetResponse])
def get_tweets(
    target_id: int,
    limit: int = Query(default=50, le=200),
    days: Optional[int] = Query(default=7, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier que la cible appartient à l'utilisateur
    target = db.query(Target).filter(Target.id == target_id, Target.user_id == current_user.id).first()
    if not target:
        return []
    
    since = datetime.utcnow() - timedelta(days=days)
    
    tweets = db.query(Tweet).filter(
        Tweet.target_id == target_id,
        Tweet.analyzed_at >= since
    ).order_by(Tweet.tweet_created_at.desc()).limit(limit).all()
    
    return tweets
=======
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet
from backend.app.services.auth import get_current_user

router = APIRouter(prefix="/tweets", tags=["tweets"])


@router.get("/{target_id}")
def get_tweets(
    target_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = (
        db.query(Target)
        .filter(Target.id == target_id, Target.user_id == current_user.id)
        .first()
    )

    if not target:
        raise HTTPException(status_code=404, detail="Cible introuvable")

    tweets = (
        db.query(Tweet)
        .filter(Tweet.target_id == target_id)
        .order_by(Tweet.tweet_created_at.desc().nullslast())
        .limit(limit)
        .all()
    )

    return tweets
>>>>>>> de7e700a57fde813194d5d256df032c07dda626c
