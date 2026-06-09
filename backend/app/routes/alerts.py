from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.alert import Alert
from backend.app.models.target import Target
from backend.app.schemas.alert import AlertCreate, AlertResponse
from backend.app.services.auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alertes"])


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier que la cible appartient à l'utilisateur
    target = db.query(Target).filter(Target.id == alert_data.target_id, Target.user_id == current_user.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    alert = Alert(
        user_id=current_user.id,
        target_id=alert_data.target_id,
        name=alert_data.name,
        sentiment=alert_data.sentiment,
        threshold=alert_data.threshold,
        is_above=alert_data.is_above
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Alert).filter(Alert.user_id == current_user.id).all()


@router.patch("/{alert_id}/toggle", response_model=AlertResponse)
def toggle_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    db.delete(alert)
    db.commit()
