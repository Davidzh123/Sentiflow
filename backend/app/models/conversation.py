from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from datetime import datetime
from backend.app.database import Base


class Conversation(Base):
    """Une conversation (fil de discussion) de l'assistant, comme dans ChatGPT."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), default="Nouvelle conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationMessage(Base):
    """Un message dans une conversation (question de l'utilisateur ou réponse de l'assistant)."""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    role = Column(String(20), default="user")  # user | assistant
    content = Column(Text, nullable=False)
    meta_json = Column(JSON, nullable=True)     # sources, mode, model, dashboard_url...
    created_at = Column(DateTime, default=datetime.utcnow)
