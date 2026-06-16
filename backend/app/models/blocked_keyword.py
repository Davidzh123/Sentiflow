from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.database import Base


class BlockedKeyword(Base):
    """Mot/thème bloqué pour la modération du RAG (géré par l'admin)."""
    __tablename__ = "blocked_keywords"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(200), nullable=False)
    category = Column(String(50), default="custom")
    created_at = Column(DateTime, default=datetime.utcnow)
