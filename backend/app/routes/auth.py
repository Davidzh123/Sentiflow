from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User)
        .filter((User.email == data.email) | (User.username == data.username))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ou username déjà utilisé",
        )

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Notifications : bienvenue + alerte admin
    try:
        from backend.app.services.notifications import notify
        notify(db, user.id, "system", "Bienvenue sur SentiFlow",
               "Votre compte est créé. Ajoutez un sujet à suivre pour commencer.")
        for a in db.query(User).filter(User.is_admin == True).all():  # noqa: E712
            if a.id != user.id:
                notify(db, a.id, "system", "Nouvel utilisateur",
                       f"{user.username} ({user.email}) vient de créer un compte.")
    except Exception:
        pass

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "plan": getattr(user, "plan", "free") or "free",
        },
    }


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "plan": getattr(user, "plan", "free") or "free",
        },
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    from backend.app.services.plans import get_features, get_ai_quota_status
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "plan": getattr(current_user, "plan", "free") or "free",
        "features": get_features(current_user),
        "quota": get_ai_quota_status(current_user),
    }


@router.get("/plan")
def my_plan(current_user: User = Depends(get_current_user)):
    """Détail de l'offre de l'utilisateur + quota du jour + catalogue des offres."""
    from backend.app.services.plans import get_features, get_ai_quota_status, PLANS
    return {
        "current": get_features(current_user),
        "quota": get_ai_quota_status(current_user),
        "catalog": PLANS,
    }


class ProfileUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    current_password: str | None = None


@router.patch("/profile")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """L'utilisateur modifie son email et/ou son mot de passe."""
    from backend.app.services.notifications import notify

    changes = []

    if data.email and data.email != current_user.email:
        existing = db.query(User).filter(User.email == data.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
        old_email = current_user.email
        current_user.email = data.email
        changes.append("email")
        notify(db, current_user.id, "system", "Email modifié",
               f"Votre email a été changé en {data.email}.")
        for a in db.query(User).filter(User.is_admin == True).all():  # noqa: E712
            if a.id != current_user.id:
                notify(db, a.id, "system", "Email utilisateur modifié",
                       f"{current_user.username} a changé son email ({old_email} → {data.email}).")

    if data.password:
        if len(data.password) < 4:
            raise HTTPException(status_code=400, detail="Mot de passe trop court.")
        current_user.hashed_password = hash_password(data.password)
        changes.append("mot de passe")
        notify(db, current_user.id, "system", "Mot de passe modifié",
               "Votre mot de passe a été mis à jour.")
        for a in db.query(User).filter(User.is_admin == True).all():  # noqa: E712
            if a.id != current_user.id:
                notify(db, a.id, "system", "Mot de passe utilisateur modifié",
                       f"{current_user.username} a changé son mot de passe.")

    if not changes:
        raise HTTPException(status_code=400, detail="Aucune modification fournie.")

    db.commit()
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "changed": changes,
    }


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Réinitialise le mot de passe à partir de l'email (DÉMO : sans vérification par email).
    En production, il faudrait un lien/token envoyé par email.
    """
    if len(data.new_password) < 4:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (min 4 caractères).")
    user = db.query(User).filter(User.email == data.email).first()
    # Réponse identique que l'email existe ou non (évite l'énumération de comptes)
    if user:
        user.hashed_password = hash_password(data.new_password)
        db.commit()
        try:
            from backend.app.services.notifications import notify
            notify(db, user.id, "system", "Mot de passe réinitialisé",
                   "Votre mot de passe a été réinitialisé depuis la page de connexion.")
        except Exception:
            pass
    return {"message": "Si un compte existe avec cet email, le mot de passe a été réinitialisé."}
