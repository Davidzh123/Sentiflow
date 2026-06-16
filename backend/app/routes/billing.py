"""
Abonnement & paiement (simulé) + factures.
Le paiement est factice : pas de vraie banque. On active l'offre, on crée une
facture et on notifie l'utilisateur.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.invoice import Invoice
from backend.app.models.user import User
from backend.app.services.auth import get_current_user
from backend.app.services.notifications import notify
from backend.app.services.plans import PLANS

router = APIRouter(prefix="/billing", tags=["Billing"])


class SubscribeRequest(BaseModel):
    plan: str = Field(..., description="free | standard | premium")
    # Champs de carte factices (non vérifiés — paiement simulé)
    card_name: str | None = None


def _next_invoice_number(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(func.count(Invoice.id)).scalar() or 0
    return f"INV-{year}-{count + 1:06d}"


def _serialize_invoice(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "number": inv.number,
        "plan": inv.plan,
        "amount_eur": inv.amount_eur,
        "status": inv.status,
        "period": inv.period,
        "created_at": str(inv.created_at) if inv.created_at else None,
    }


@router.post("/subscribe")
def subscribe(
    data: SubscribeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Offre invalide. Choix : {list(PLANS.keys())}")

    old_plan = current_user.plan or "free"
    current_user.plan = data.plan
    db.commit()

    amount = PLANS[data.plan]["price_eur"]
    invoice_data = None

    if data.plan == "free":
        notify(db, current_user.id, "subscription", "Offre modifiée",
               f"Votre offre est passée de {PLANS.get(old_plan, {}).get('label', old_plan)} à Free.")
    else:
        # Paiement simulé réussi -> facture
        inv = Invoice(
            user_id=current_user.id,
            number=_next_invoice_number(db),
            plan=data.plan,
            amount_eur=amount,
            status="paid",
            period="mensuel",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        invoice_data = _serialize_invoice(inv)

        action = "Réabonnement" if old_plan == data.plan else "Abonnement"
        notify(db, current_user.id, "payment", f"{action} confirmé",
               f"Paiement de {amount}€ accepté pour l'offre {PLANS[data.plan]['label']}. Facture {inv.number} disponible.")
        notify(db, current_user.id, "subscription", "Offre activée",
               f"L'offre {PLANS[data.plan]['label']} est maintenant active.")

    return {
        "plan": current_user.plan,
        "invoice": invoice_data,
        "message": f"Offre {PLANS[data.plan]['label']} activée.",
    }


@router.get("/invoices")
def my_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.id.desc())
        .all()
    )
    return [_serialize_invoice(i) for i in rows]


@router.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id, Invoice.user_id == current_user.id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    from backend.app.services.pdf_generator import generate_invoice_pdf
    pdf_bytes = generate_invoice_pdf(
        number=inv.number,
        username=current_user.username,
        email=current_user.email,
        plan=PLANS.get(inv.plan, {}).get("label", inv.plan),
        amount=inv.amount_eur,
        period=inv.period,
        created_at=str(inv.created_at) if inv.created_at else "",
    )
    if pdf_bytes is None:
        raise HTTPException(status_code=500, detail="Generation PDF indisponible")

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={inv.number}.pdf"},
    )
