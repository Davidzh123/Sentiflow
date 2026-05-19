from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.services.auth import get_current_user
from backend.app.services.local_llm import ask_local_llm


router = APIRouter(prefix="/llm", tags=["LLM local"])


class LLMAskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    target_ids: List[int]
    days: int = Field(default=7, ge=1, le=90)
    generate_dashboard: bool = True


@router.post("/ask")
def ask_llm(
    payload: LLMAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return ask_local_llm(
            db=db,
            user_id=current_user.id,
            question=payload.question,
            target_ids=payload.target_ids,
            days=payload.days,
            generate_dashboard=payload.generate_dashboard,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))