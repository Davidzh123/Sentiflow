# 📊 SentiFlow - Analyse de Sentiments Twitter

Plateforme d'analyse de sentiments Twitter en temps réel avec ML, Kafka et React.

## Architecture

| Service | Technologie | Port |
|---------|------------|------|
| Frontend | React + Nginx | 3000 |
| API | FastAPI | 8000 |
| Base de données | PostgreSQL | 5432 |
| Cache/Queue | Redis | 6379 |
| Streaming | Kafka | 9092 |
| Planificateur | Celery Beat | - |
| Worker | Celery Worker | - |
| Consumer | Kafka Consumer | - |
| Zookeeper | Zookeeper | 2181 |

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) et Docker Compose
- Git

C'est tout. Docker installe automatiquement toutes les dépendances (Python, Node.js, etc.).

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/votre-repo/sentiflow.git
cd sentiflow

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et remplir :
# - TWITTER_API_KEY : clé API twitterapi.io
# - JWT_SECRET : générer avec python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Lancement

```bash
# Lancer tous les services (premier lancement ~10-15 min)
docker compose up -d --build

# Vérifier que tout tourne
docker compose ps
```

Ouvrir dans le navigateur :
- Frontend : http://localhost:3000
- API docs : http://localhost:8000/docs

## Développement local (frontend)

Pour le développement du frontend React sans Docker :

```bash
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

Le frontend sera sur http://localhost:3000 avec hot-reload.

## Commandes utiles

```bash
# Voir les logs d'un service
docker compose logs api --tail 20
docker compose logs celery-worker --tail 20
docker compose logs kafka-consumer --tail 20

# Redémarrer un service
docker compose restart api

# Accéder à la base de données
docker compose exec db psql -U sentiflow -d sentiflow

# Arrêter tout
docker compose down

# Tout reconstruire
docker compose up -d --build
```

## Créer un compte admin

```bash
# Créer un compte via le frontend, puis :
docker compose exec db psql -U sentiflow -d sentiflow -c "UPDATE users SET is_admin = true WHERE email = 'votre@email.fr';"
```

## Stack technique

- Backend : FastAPI, SQLAlchemy, JWT (Python/UV)
- Frontend : React, Axios, Recharts
- ML : XLM-RoBERTa fine-tuné (HuggingFace)
- Streaming : Apache Kafka
- Tâches : Celery + Redis
- BDD : PostgreSQL
- Conteneurisation : Docker Compose
