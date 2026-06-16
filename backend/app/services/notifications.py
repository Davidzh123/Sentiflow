"""
Centre de notifications in-app.
Helper unique `notify(...)` appelé depuis les différents événements de l'app
(abonnement, paiement, ticket, export PDF, alerte, collecte, entraînement).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.notification import Notification

logger = logging.getLogger("sentiflow.notifications")


def notify(db: Session, user_id: Optional[int], type: str, title: str, message: str = "") -> None:
    """Crée une notification. Ne lève jamais d'erreur (best-effort)."""
    if not user_id:
        return
    try:
        n = Notification(user_id=user_id, type=type, title=title, message=message or "")
        db.add(n)
        db.commit()
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("notify failed: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass
