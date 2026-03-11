# SentiFlow 📊

Plateforme d'analyse de sentiments Twitter avec LLM et Deep Reinforcement Learning.

## Structure du projet

```
sentiflow/
├── backend/          # API FastAPI
├── frontend/         # Interface Streamlit
├── data/
│   ├── raw/          # Données brutes
│   ├── processed/    # Données nettoyées
│   └── models/       # Modèles sauvegardés
├── services/
│   ├── sentiment/    # CamemBERT fine-tuné
│   ├── llm/          # Transformer from scratch
│   └── drl/          # Deep RL
├── features/         # Feature engineering, pipelines ML
├── tests/            # Tests pytest
└── docs/             # Documentation
```

## Installation avec UV

```bash
# Installer uv
pip install uv

# Créer l'environnement et installer les dépendances
uv sync

# Activer l'environnement
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

## Lancement rapide

```bash
# Avec Docker
docker-compose up -d

# Sans Docker (dev local)
# Terminal 1 - API
uvicorn backend.app.main:app --reload

# Terminal 2 - Frontend
streamlit run frontend/app.py
```

## Tests

```bash
pytest tests/ -v
```

## URLs

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Frontend: http://localhost:8501
