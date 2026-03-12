import httpx
import streamlit as st
from typing import Optional
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")


def get_headers() -> dict:
    """Retourne les headers avec le token JWT"""
    if st.session_state.get("token"):
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def login(email: str, password: str) -> tuple[bool, str, Optional[dict]]:
    """Connexion utilisateur"""
    try:
        response = httpx.post(f"{API_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return True, "Connexion réussie", response.json()
        return False, "Email ou mot de passe incorrect", None
    except Exception as e:
        return False, f"Erreur de connexion à l'API: {str(e)}", None


def register(email: str, username: str, password: str) -> tuple[bool, str]:
    """Inscription utilisateur"""
    try:
        response = httpx.post(f"{API_URL}/auth/register", json={
            "email": email,
            "username": username,
            "password": password
        })
        if response.status_code == 201:
            return True, "Inscription réussie !"
        elif response.status_code == 400:
            return False, response.json().get("detail", "Email ou nom d'utilisateur déjà utilisé")
        return False, "Erreur serveur"
    except Exception as e:
        return False, f"Erreur de connexion à l'API: {str(e)}"


def get_me() -> Optional[dict]:
    """Récupère l'utilisateur courant"""
    try:
        response = httpx.get(f"{API_URL}/auth/me", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def get_targets() -> list:
    """Récupère les cibles de l'utilisateur"""
    try:
        response = httpx.get(f"{API_URL}/targets/", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def create_target(name: str, target_type: str) -> Optional[dict]:
    """Crée une nouvelle cible"""
    try:
        response = httpx.post(f"{API_URL}/targets/", headers=get_headers(), json={
            "name": name,
            "target_type": target_type
        })
        if response.status_code == 201:
            return response.json()
        return None
    except Exception:
        return None


def delete_target(target_id: int) -> bool:
    """Supprime une cible"""
    try:
        response = httpx.delete(f"{API_URL}/targets/{target_id}", headers=get_headers())
        return response.status_code == 204
    except Exception:
        return False


def verify_target(target_id: int) -> Optional[dict]:
    """Vérifie si une cible existe sur Twitter"""
    try:
        response = httpx.get(f"{API_URL}/twitter/verify/{target_id}", headers=get_headers(), timeout=30.0)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def collect_tweets(target_id: int) -> tuple[bool, str, Optional[dict]]:
    """Collecte les tweets pour une cible"""
    try:
        response = httpx.post(f"{API_URL}/twitter/collect/{target_id}", headers=get_headers(), timeout=30.0)
        if response.status_code == 200:
            return True, "OK", response.json()
        else:
            detail = response.json().get("detail", response.text)
            return False, detail, None
    except Exception as e:
        return False, str(e), None


def get_analysis(target_id: int, days: int = 7) -> Optional[dict]:
    """Récupère l'analyse de sentiment"""
    try:
        response = httpx.get(
            f"{API_URL}/analysis/{target_id}",
            headers=get_headers(),
            params={"days": days}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def get_alerts() -> list:
    """Récupère les alertes"""
    try:
        response = httpx.get(f"{API_URL}/alerts/", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def create_alert(target_id: int, name: str, sentiment: str, threshold: float, is_above: bool) -> Optional[dict]:
    """Crée une alerte"""
    try:
        response = httpx.post(f"{API_URL}/alerts/", headers=get_headers(), json={
            "target_id": target_id,
            "name": name,
            "sentiment": sentiment,
            "threshold": threshold,
            "is_above": is_above
        })
        if response.status_code == 201:
            return response.json()
        return None
    except Exception:
        return None
