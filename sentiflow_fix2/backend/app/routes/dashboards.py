from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.generated_dashboard import GeneratedDashboard
from backend.app.models.user import User
from backend.app.services.auth import get_current_user


router = APIRouter(prefix="/dashboards", tags=["Dashboards générés"])


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

    return serialize_dashboard(dashboard, include_config=True)


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
