import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from components.api import get_targets, create_target, delete_target, verify_target, collect_tweets

st.title("🎯 Gérer les cibles")

if not st.session_state.get("token"):
    st.warning("Veuillez vous connecter")
    st.stop()

# Formulaire d'ajout
st.subheader("Ajouter une cible")
with st.form("add_target"):
    col1, col2 = st.columns([3, 1])
    with col1:
        name = st.text_input("Hashtag ou compte", placeholder="#MachineLearning ou @elonmusk")
    with col2:
        target_type = st.selectbox("Type", ["hashtag", "account"])
    
    submitted = st.form_submit_button("Ajouter")
    if submitted and name:
        result = create_target(name, target_type)
        if result:
            st.success(f"Cible '{name}' ajoutée !")
            st.rerun()
        else:
            st.error("Erreur lors de l'ajout")

# Liste des cibles
st.subheader("Cibles actuelles")
targets = get_targets()

if not targets:
    st.info("Aucune cible configurée")
else:
    for target in targets:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        with col1:
            icon = "#️⃣" if target["target_type"] == "hashtag" else "👤"
            st.write(f"{icon} {target['name']}")
        with col2:
            st.caption(target["target_type"])
        with col3:
            if st.button("✅ Vérifier", key=f"verify_{target['id']}"):
                with st.spinner("Vérification..."):
                    result = verify_target(target["id"])
                    if result:
                        if result.get("exists"):
                            st.success(f"✅ Existe sur Twitter")
                        else:
                            st.warning(f"❌ Non trouvé sur Twitter")
                    else:
                        st.error("Erreur API")
        with col4:
            if st.button("📥 Collecter", key=f"collect_{target['id']}"):
                with st.spinner("Collecte en cours..."):
                    success, message, result = collect_tweets(target["id"])
                    if success:
                        st.success(f"✅ {result['saved']} tweets collectés")
                    else:
                        st.error(f"Erreur: {message}")
        with col5:
            if st.button("🗑️", key=f"del_{target['id']}"):
                if delete_target(target["id"]):
                    st.rerun()
