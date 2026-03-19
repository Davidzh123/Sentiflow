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

## 🤖 Modèle de Sentiment (ML)

### Architecture
Le projet utilise un modèle **XLM-RoBERTa** fine-tuné pour la classification d'émotions multilingue (français/anglais).

**6 émotions détectées :**
- 😊 Joie
- 😢 Tristesse  
- 😠 Colère
- 😨 Peur
- 😲 Surprise
- ❤️ Amour

### Datasets utilisés
- `dair-ai/emotion` - 16 000 tweets annotés
- `go_emotions` (Google) - 58 000 exemples supplémentaires

### Tester le modèle

```bash
# Test rapide
python -c "from services.sentiment.model import get_analyzer; a = get_analyzer(); print(a.predict('Je suis heureux'))"

# Test sur dataset
python scripts/test_model.py

# Évaluation complète (accuracy, F1-score)
python scripts/evaluate_model.py
```

### Fine-tuning (améliorer le modèle)

Le notebook `scripts/finetune_colab.ipynb` permet d'entraîner le modèle sur Google Colab (GPU gratuit).

**Étapes :**
1. Ouvrir https://colab.research.google.com
2. File → Upload notebook → `scripts/finetune_colab.ipynb`
3. Runtime → Change runtime type → **GPU**
4. Exécuter toutes les cellules
5. Télécharger le ZIP du modèle
6. Décompresser dans `data/models/sentiflow_emotion_model/`

**Résultats attendus :** ~92% accuracy, ~91% F1-score

### Structure ML

```
services/sentiment/
├── __init__.py
└── model.py          # SentimentAnalyzer (inference)

scripts/
├── test_model.py     # Test sur quelques tweets
├── evaluate_model.py # Évaluation avec métriques
└── finetune_colab.ipynb  # Fine-tuning sur Colab

data/
├── raw/              # Datasets bruts (CSV)
├── processed/        # Données nettoyées
└── models/           # Modèles fine-tunés (local)
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
│   └── sentiment/    # Modèle d'émotions
├── scripts/          # Scripts ML (test, eval, finetune)
├── features/         # Pipelines ML
├── tests/            # pytest
├── data/             # Datasets et modèles
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

## 📊 Technologies

- **Backend** : FastAPI, SQLAlchemy, PostgreSQL
- **Frontend** : Streamlit, Plotly
- **ML** : PyTorch, Transformers (HuggingFace), XLM-RoBERTa
- **Infra** : Docker, Redis
- **API Twitter** : twitterapi.io
