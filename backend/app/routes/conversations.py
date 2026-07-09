"""
Historique des conversations de l'assistant (façon ChatGPT).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.conversation import Conversation, ConversationMessage
from backend.app.models.user import User
from backend.app.services.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


def _serialize(c: Conversation) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "created_at": str(c.created_at) if c.created_at else None,
        "updated_at": str(c.updated_at) if c.updated_at else None,
    }


def _serialize_msg(m: ConversationMessage) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "meta": m.meta_json or {},
        "created_at": str(m.created_at) if m.created_at else None,
    }


@router.get("")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_serialize(c) for c in rows]


@router.post("")
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = Conversation(user_id=current_user.id, title=(data.title or "Nouvelle conversation")[:255])
    db.add(c)
    db.commit()
    db.refresh(c)
    return _serialize(c)


@router.get("/{conv_id}")
def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = db.query(Conversation).filter(
        Conversation.id == conv_id, Conversation.user_id == current_user.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    msgs = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conv_id)
        .order_by(ConversationMessage.id.asc())
        .all()
    )
    return {**_serialize(c), "messages": [_serialize_msg(m) for m in msgs]}


@router.patch("/{conv_id}")
def rename_conversation(
    conv_id: int,
    data: RenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = db.query(Conversation).filter(
        Conversation.id == conv_id, Conversation.user_id == current_user.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    c.title = data.title[:255]
    db.commit()
    return _serialize(c)


@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = db.query(Conversation).filter(
        Conversation.id == conv_id, Conversation.user_id == current_user.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conv_id).delete()
    db.delete(c)
    db.commit()
    return {"deleted": conv_id}


# Helper appelé par la route assistant pour enregistrer un échange
def save_exchange(
    db: Session,
    user_id: int,
    conversation_id: Optional[int],
    question: str,
    answer: str,
    meta: Optional[dict] = None,
) -> int:
    """Enregistre (question + réponse) dans une conversation. Crée la conversation si besoin."""
    conv = None
    if conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        ).first()
    if not conv:
        conv = Conversation(user_id=user_id, title=(question[:60] or "Nouvelle conversation"))
        db.add(conv)
        db.commit()
        db.refresh(conv)

    db.add(ConversationMessage(conversation_id=conv.id, role="user", content=question))
    db.add(ConversationMessage(conversation_id=conv.id, role="assistant", content=answer, meta_json=meta or {}))
    conv.updated_at = datetime.utcnow()
    db.commit()
    return conv.id
