from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet
from backend.app.models.alert import Alert
from backend.app.services.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie que l'utilisateur est admin"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return current_user


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Statistiques globales (admin only)"""
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "targets": db.query(func.count(Target.id)).filter(Target.user_id == current_user.id).scalar(),
        "tweets": db.query(func.count(Tweet.id)).join(Target).filter(Target.user_id == current_user.id).scalar(),
        "alerts": db.query(func.count(Alert.id)).filter(Alert.user_id == current_user.id).scalar()
    }


@router.delete("/tweets/{target_id}")
def delete_tweets_by_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Supprime tous les tweets d'une cible"""
    # Vérifier que la cible appartient à l'admin
    target = db.query(Target).filter(Target.id == target_id, Target.user_id == current_user.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    deleted = db.query(Tweet).filter(Tweet.target_id == target_id).delete()
    db.commit()
    
    return {"deleted": deleted, "target": target.name}


@router.delete("/tweets/all")
def delete_all_tweets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Supprime tous les tweets de l'utilisateur admin"""
    # Récupérer les IDs des cibles de l'admin
    target_ids = [t.id for t in db.query(Target).filter(Target.user_id == current_user.id).all()]
    
    if not target_ids:
        return {"deleted": 0}
    
    deleted = db.query(Tweet).filter(Tweet.target_id.in_(target_ids)).delete(synchronize_session=False)
    db.commit()
    
    return {"deleted": deleted}


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Liste tous les utilisateurs (admin only)"""
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "username": u.username, "is_admin": u.is_admin} for u in users]


@router.patch("/users/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Promouvoir/rétrograder un utilisateur admin"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas modifier votre propre statut")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.is_admin = not user.is_admin
    db.commit()
    
    return {"id": user.id, "username": user.username, "is_admin": user.is_admin}
