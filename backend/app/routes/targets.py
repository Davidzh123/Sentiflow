from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.target import Target, TargetType
from backend.app.schemas.target import TargetCreate, TargetResponse
from backend.app.services.auth import get_current_user

router = APIRouter(prefix="/targets", tags=["Cibles"])


def build_query(name: str, target_type: TargetType) -> str:
    """Construit la requête Twitter à partir du nom"""
    if target_type == TargetType.HASHTAG:
        return name if name.startswith("#") else f"#{name}"
    else:
        return f"from:{name.replace('@', '')}"


@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(
    target_data: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = Target(
        user_id=current_user.id,
        name=target_data.name,
        target_type=target_data.target_type,
        query=build_query(target_data.name, target_data.target_type)
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.get("/", response_model=List[TargetResponse])
def get_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Target).filter(Target.user_id == current_user.id).all()


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = db.query(Target).filter(Target.id == target_id, Target.user_id == current_user.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    db.delete(target)
    db.commit()
