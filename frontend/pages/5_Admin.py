import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from components.api import get_headers, API_URL
import httpx

st.title("⚙️ Administration")

if not st.session_state.get("token"):
    st.warning("Veuillez vous connecter")
    st.stop()

# Vérifier si admin
if not st.session_state.get("user", {}).get("is_admin", False):
    st.error("🚫 Accès réservé aux administrateurs")
    st.stop()

st.success(f"👑 Connecté en tant qu'admin: **{st.session_state.user['username']}**")

st.subheader("Gestion des données")

# Stats
st.write("### 📊 Statistiques")
try:
    response = httpx.get(f"{API_URL}/admin/stats", headers=get_headers())
    if response.status_code == 200:
        stats = response.json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Utilisateurs", stats.get("users", 0))
        col2.metric("Cibles", stats.get("targets", 0))
        col3.metric("Tweets", stats.get("tweets", 0))
        col4.metric("Alertes", stats.get("alerts", 0))
except:
    st.info("Stats non disponibles")

st.divider()

# Gestion des utilisateurs
st.write("### 👥 Gestion des utilisateurs")
try:
    response = httpx.get(f"{API_URL}/admin/users", headers=get_headers())
    if response.status_code == 200:
        users = response.json()
        for user in users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                role = "👑 Admin" if user["is_admin"] else "👤 User"
                st.write(f"{role} - **{user['username']}** ({user['email']})")
            with col2:
                if user["id"] != st.session_state.user["id"]:
                    btn_label = "Rétrograder" if user["is_admin"] else "Promouvoir"
                    if st.button(btn_label, key=f"toggle_{user['id']}"):
                        resp = httpx.patch(f"{API_URL}/admin/users/{user['id']}/toggle-admin", headers=get_headers())
                        if resp.status_code == 200:
                            st.rerun()
except Exception as e:
    st.error(f"Erreur: {e}")

st.divider()

# Supprimer tous les tweets d'une cible
st.write("### 🗑️ Supprimer les tweets d'une cible")
try:
    response = httpx.get(f"{API_URL}/targets/", headers=get_headers())
    if response.status_code == 200:
        targets = response.json()
        if targets:
            target_options = {t["id"]: f"{t['name']} ({t['target_type']})" for t in targets}
            selected_target = st.selectbox("Sélectionner une cible", options=list(target_options.keys()), format_func=lambda x: target_options[x])
            
            if st.button("🗑️ Supprimer tous les tweets de cette cible", type="secondary"):
                response = httpx.delete(f"{API_URL}/admin/tweets/{selected_target}", headers=get_headers())
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['deleted']} tweets supprimés")
                else:
                    st.error("Erreur lors de la suppression")
        else:
            st.info("Aucune cible")
except Exception as e:
    st.error(f"Erreur: {e}")

st.divider()

# Supprimer TOUS les tweets
st.write("### ⚠️ Zone dangereuse")
with st.expander("Supprimer TOUTES les données"):
    st.warning("Cette action est irréversible !")
    
    confirm = st.text_input("Tapez 'SUPPRIMER' pour confirmer")
    
    if st.button("🗑️ Supprimer TOUS mes tweets", type="primary", disabled=confirm != "SUPPRIMER"):
        response = httpx.delete(f"{API_URL}/admin/tweets/all", headers=get_headers())
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ {result['deleted']} tweets supprimés")
        else:
            st.error("Erreur lors de la suppression")
