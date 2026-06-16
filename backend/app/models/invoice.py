from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime
from backend.app.database import Base


class Invoice(Base):
    """Facture d'abonnement (paiement simulé)."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    number = Column(String(40), unique=True, nullable=False)  # ex: INV-2026-000012
    plan = Column(String(20), nullable=False)                 # standard | premium
    amount_eur = Column(Float, nullable=False)
    status = Column(String(20), default="paid")               # paid
    period = Column(String(20), default="mensuel")
    created_at = Column(DateTime, default=datetime.utcnow)
