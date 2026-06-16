from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from datetime import datetime
from backend.app.database import Base


class Notification(Base):
    """Notification in-app : tout ce qui se passe dans l'app pour l'utilisateur."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    # type : collect, training, subscription, payment, pdf_export, ticket, alert, system
    type = Column(String(30), default="system")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
