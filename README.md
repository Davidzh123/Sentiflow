# SentiFlow 📊

Plateforme d'analyse de sentiments Twitter avec LLM et Deep Reinforcement Learning.

## 🚀 Installation rapide

### Prérequis
- Docker Desktop
- Git

### Option 1 : Tout avec Docker (recommandé pour production/partage)

```bash
# Cloner le repo
git clone https://github.com/ton-username/sentiflow.git
cd sentiflow

# Créer le fichier .env
cp .env.example .env
# Éditer .env et ajouter TWITTER_API_KEY

# Lancer TOUT (BDD + Redis + API + Frontend)
docker compose up -d

# Vérifier que tout tourne
docker compose ps
```

Accéder à :
- Frontend : http://localhost:8501
- API Swagger : http://localhost:8000/docs

### Option 2 : Dev local (pour développer)

```bash
# Installer uv
pip install uv

# Installer les dépendances
uv sync

# Lancer seulement BDD + Redis
docker compose up -d db redis

# Terminal 1 - API
uv run uvicorn backend.app.main:app --reload

# Terminal 2 - Frontend
uv run streamlit run frontend/app.py
```

## 🌿 Git - Workflow pour collaborateurs

### Récupérer le projet

```bash
git clone https://github.com/ton-username/sentiflow.git
cd sentiflow
```

### Mettre à jour son code

```bash
git pull origin main
```

### Créer une nouvelle feature

```bash
git checkout -b feature/ma-feature
# ... travailler ...
git add .
git commit -m "feat: description"
git push origin feature/ma-feature
```

## 📁 Structure du projet

```
sentiflow/
├── backend/          # API FastAPI
│   ├── Dockerfile
│   └── app/
│       ├── routes/   # auth, targets, twitter, admin
│       ├── models/   # User, Target, Tweet, Alert
│       └── services/ # Auth, Twitter client
├── frontend/         # Interface Streamlit
│   ├── Dockerfile
│   ├── app.py
│   └── pages/        # Login, Dashboard, Cibles, Admin
├── services/         # ML (sentiment, llm, drl)
├── features/         # Pipelines ML
├── tests/            # pytest
├── docker-compose.yml
└── .env.example
```

## 🧪 Tests

```bash
uv run pytest tests/ -v
```

## 🔗 URLs

- Frontend : http://localhost:8501
- API : http://localhost:8000
- Swagger : http://localhost:8000/docs

## 👥 Rôles utilisateurs

- **User** : Créer cibles, collecter tweets, dashboard
- **Admin** : Gérer utilisateurs, supprimer données

Devenir admin :
```bash
docker compose exec db psql -U sentiflow -d sentiflow -c "UPDATE users SET is_admin = TRUE WHERE email = 'ton-email';"
```

## ☁️ Déploiement AWS

```bash
# Build et push les images
docker compose build

# Sur AWS EC2 :
# 1. Installer Docker
# 2. Cloner le repo
# 3. Créer .env avec les vraies clés
# 4. docker compose up -d
```
