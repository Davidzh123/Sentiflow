# 📊 SentiFlow — Analyse intelligente de sentiments Twitter

SentiFlow est une plateforme complète de collecte, d’analyse et de visualisation de tweets. Elle combine une API FastAPI, un frontend React, un pipeline Kafka/Celery, un modèle de classification des émotions et un assistant capable de piloter la collecte et de générer automatiquement des dashboards et des rapports PDF.

## Fonctionnalités principales

- Collecte de tweets par hashtag, compte ou mot-clé via `twitterapi.io`.
- Analyse de sentiments et d’émotions : joie, tristesse, colère, peur, surprise et neutre.
- Analyse temporelle sur une période précise.
- Comparaison de plusieurs cibles.
- Assistant conversationnel pour lancer une collecte, analyser les résultats et créer un dashboard.
- Garde-fous déterministes autour du petit Transformer afin de respecter la cible, la période et les actions explicitement demandées.
- Dashboards interactifs avec indicateurs, graphiques, évolution temporelle, mots-clés et tweets représentatifs.
- Exports PDF professionnels avec couverture, KPI, graphiques, tableaux, synthèse et pagination.
- Alertes, notifications et suivi des variations de sentiment.
- Feedback utilisateur pour améliorer les prédictions.
- RAG et requêtes en langage naturel.
- Gestion des utilisateurs, abonnements et administration.
- Suivi des expériences ML avec MLflow.

## Architecture

| Service | Technologie | Port local |
|---|---|---:|
| Frontend | React + Nginx | `5173` |
| API | FastAPI | `8000` |
| Documentation API | Swagger UI | `8000/docs` |
| Base de données | PostgreSQL + pgvector | `5432` |
| Cache et file de tâches | Redis | `6379` |
| Streaming | Kafka | `9092` |
| Coordination Kafka | Zookeeper | `2181` |
| Worker asynchrone | Celery Worker | — |
| Planificateur | Celery Beat | — |
| Analyse temps réel | Kafka Consumer | — |
| Suivi ML | MLflow | `5000` |

## Stack technique

- **Backend :** Python 3.11, FastAPI, SQLAlchemy, Pydantic, JWT
- **Frontend :** React, Axios, Recharts
- **Machine Learning :** PyTorch, Transformers, XLM-RoBERTa, scikit-learn
- **Assistant :** petit Transformer local, règles sémantiques et LLM externes optionnels
- **Streaming :** Apache Kafka
- **Tâches asynchrones :** Celery et Redis
- **Base de données :** PostgreSQL et pgvector
- **MLOps :** MLflow
- **PDF :** fpdf2 et polices DejaVu
- **Déploiement :** Docker Compose

## Prérequis

- Docker Desktop ou Docker Engine avec Docker Compose
- Git
- Une clé API `twitterapi.io`

Toutes les dépendances Python et JavaScript sont installées automatiquement dans les conteneurs.

## Installation

```bash
git clone https://github.com/Davidzh123/Sentiflow.git
cd Sentiflow
cp .env.example .env
```

Sous PowerShell :

```powershell
Copy-Item .env.example .env
```

Compléter ensuite le fichier `.env` :

```env
# Obligatoire pour la collecte Twitter
TWITTER_API_KEY=votre_cle_twitterapi_io

# Obligatoire en production
JWT_SECRET=votre_secret_jwt

# Optionnels pour certaines fonctions LLM
MISTRAL_API_KEY=
GROQ_API_KEY=
```

Pour générer un secret JWT :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Ne jamais versionner le fichier `.env`.

## Lancement

```bash
docker compose up -d --build
```

Vérifier l’état des services :

```bash
docker compose ps
```

Accès principaux :

- Application : <http://localhost:5173>
- API : <http://localhost:8000>
- Documentation Swagger : <http://localhost:8000/docs>
- MLflow : <http://localhost:5000>

## Utilisation

### 1. Créer une cible

Depuis la page **Cibles**, ajouter un hashtag, un compte ou un mot-clé à surveiller.

Exemples :

```text
#Nice
@OpenAI
voiture électrique
```

### 2. Collecter et analyser

La collecte peut être lancée depuis l’interface ou depuis l’assistant.

Exemples de requêtes :

```text
Récupère les tweets des 2 derniers jours du #Nice.
Analyse les nouveaux tweets de @OpenAI.
Compare #Tesla et #Renault sur les 7 derniers jours.
Crée un dashboard sur #cinema depuis hier.
Montre-moi les tweets les plus négatifs sur #Paris.
```

Pour une demande explicite de collecte, SentiFlow :

1. identifie la cible écrite par l’utilisateur ;
2. extrait la période demandée ;
3. crée la cible si elle n’existe pas ;
4. relance réellement la collecte ;
5. ignore les doublons déjà présents ;
6. analyse les nouveaux tweets ;
7. génère la synthèse et le dashboard demandés.

### 3. Consulter le dashboard

Les dashboards peuvent afficher :

- le nombre de tweets analysés ;
- la répartition des sentiments ;
- le score de sentiment global ;
- la confiance moyenne du modèle ;
- l’évolution temporelle ;
- les différences entre plusieurs cibles ;
- les mots-clés récurrents ;
- des tweets représentatifs ;
- une synthèse générée automatiquement.

## Assistant et garde-fous LLM

Le petit Transformer local peut parfois proposer une intention ou des paramètres incorrects. SentiFlow applique donc une couche de garde-fous déterministes après sa prédiction.

Les éléments explicitement écrits dans la demande utilisateur sont prioritaires :

- `#hashtag` ou `@compte` ne peuvent pas être remplacés par une cible inventée ;
- `2 derniers jours` est converti en `days: 2` ;
- les verbes `récupère`, `collecte` ou `relance` déclenchent `collect_tweets` ;
- une émotion non demandée, comme `colere` ou `amour`, est supprimée ;
- une collecte explicite utilise `force_refresh: true`.

Exemple de plan attendu :

```json
{
  "intent": "collect_analyze_summarize",
  "targets": ["#nice"],
  "days": 2,
  "actions": [
    "create_missing_targets",
    "collect_tweets",
    "analyze_sentiments",
    "summarize",
    "generate_dashboard"
  ],
  "sentiment_filter": null,
  "force_refresh": true,
  "planner_guardrail_version": "semantic_guardrails_v3"
}
```

Vérifier la version chargée :

```powershell
Invoke-RestMethod http://localhost:8000/llm/model-info | ConvertTo-Json
```

La réponse doit contenir :

```json
"guardrail_version": "semantic_guardrails_v3"
```

## Exports PDF

Depuis un dashboard, cliquer sur **Exporter en PDF**.

Les rapports comprennent notamment :

- une couverture SentiFlow ;
- la cible et la période réellement analysées ;
- des cartes KPI ;
- la répartition globale des sentiments ;
- la comparaison des cibles ;
- les graphiques de sentiments ;
- l’évolution temporelle ;
- les mots-clés principaux ;
- des tweets représentatifs diversifiés par sentiment ;
- la synthèse IA ;
- une pagination et des pieds de page.

La période du rapport respecte `plan_json.days`. Un rapport demandé sur les deux derniers jours n’intègre donc pas automatiquement tous les anciens tweets de la cible.

Après une modification du générateur PDF ou du Dockerfile, reconstruire l’API pour installer les polices Unicode :

```bash
docker compose up -d --build api
```

## Tests

Lancer tous les tests :

```bash
pytest -q
```

Tests des garde-fous et de la collecte :

```bash
pytest -q tests/test_llm_planner_guardrails.py tests/test_twitter_service.py
```

Tests des exports PDF :

```bash
pytest -q tests/test_pdf_generator.py
```

Sous PowerShell, si les imports du projet ne sont pas trouvés :

```powershell
$env:PYTHONPATH = "."
pytest -q
```

## Commandes Docker utiles

```bash
# Voir l’état des conteneurs
docker compose ps

# Voir les logs principaux
docker compose logs -f api kafka-consumer celery-worker

# Logs de l’API
docker compose logs api --tail 100

# Logs de la collecte asynchrone
docker compose logs celery-worker --tail 100

# Logs de l’analyse temps réel
docker compose logs kafka-consumer --tail 100

# Redémarrer uniquement l’API
docker compose restart api

# Reconstruire uniquement le frontend
docker compose up -d --build frontend

# Reconstruire uniquement l’API
docker compose up -d --build api

# Reconstruire toute l’application
docker compose up -d --build

# Arrêter l’application
docker compose down

# Arrêter et supprimer les volumes de données
# Attention : cette commande supprime la base PostgreSQL.
docker compose down -v
```

## Commandes PostgreSQL utiles

Ouvrir PostgreSQL :

```bash
docker compose exec db psql -U sentiflow -d sentiflow
```

Compter les tweets collectés et analysés :

```bash
docker compose exec db psql -U sentiflow -d sentiflow -c "SELECT COUNT(*) AS total, COUNT(CASE WHEN sentiment IS NOT NULL THEN 1 END) AS analyses FROM tweets;"
```

Afficher les derniers tweets analysés :

```bash
docker compose exec db psql -U sentiflow -d sentiflow -c "SELECT author_username, sentiment, ROUND(confidence::numeric, 2) AS confiance, LEFT(text, 80) AS tweet FROM tweets ORDER BY id DESC LIMIT 10;"
```

Afficher le volume par utilisateur et par cible :

```bash
docker compose exec db psql -U sentiflow -d sentiflow -c "SELECT u.username, t.name, COUNT(tw.id) AS tweets FROM targets t LEFT JOIN tweets tw ON tw.target_id = t.id JOIN users u ON u.id = t.user_id GROUP BY u.username, t.name ORDER BY tweets DESC;"
```

## Administration

### Créer un administrateur

Créer d’abord le compte depuis l’application, puis exécuter :

```bash
docker compose exec db psql -U sentiflow -d sentiflow -c "UPDATE users SET is_admin = true WHERE email = 'votre@email.fr';"
```

### Modifier un mot de passe

Générer le hash :

```bash
docker compose exec api python -c "from backend.app.services.auth import hash_password; print(hash_password('nouveau_mot_de_passe'))"
```

Puis mettre à jour l’utilisateur dans PostgreSQL :

```sql
UPDATE users
SET hashed_password = 'HASH_GENERE'
WHERE email = 'votre@email.fr';
```

## Développement local du frontend

```bash
cd frontend
npm install
```

Sous PowerShell :

```powershell
$env:REACT_APP_API_URL = "http://localhost:8000"
npm start
```

Sous Linux ou macOS :

```bash
REACT_APP_API_URL=http://localhost:8000 npm start
```

## Structure simplifiée du projet

```text
SentiFlow/
├── backend/
│   └── app/
│       ├── routes/          # Endpoints FastAPI
│       ├── services/        # Twitter, ML, LLM, PDF, RAG, notifications
│       ├── models/          # Modèles SQLAlchemy
│       ├── schemas/         # Schémas Pydantic
│       ├── celery_app.py    # Configuration Celery
│       ├── kafka_consumer.py
│       └── main.py
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       └── services/
├── services/                # Modèles et ressources supplémentaires
├── tests/                   # Tests unitaires et d’intégration
├── docker-compose.yml
├── Dockerfile.backend
├── pyproject.toml
└── README.md
```

## Dépannage

### La collecte indique « données déjà disponibles » sans récupérer de nouveaux tweets

1. Vérifier que l’API utilise `semantic_guardrails_v3`.
2. Redémarrer l’API :

```bash
docker compose restart api
```

3. Consulter les logs :

```bash
docker compose logs api --tail 100
```

4. Vérifier que `TWITTER_API_KEY` est bien disponible dans le conteneur :

```bash
docker compose exec api env | grep TWITTER_API_KEY
```

Sous PowerShell :

```powershell
docker compose exec api printenv TWITTER_API_KEY
```

### Aucun tweet n’est retourné

Vérifier :

- la validité de la clé `twitterapi.io` ;
- l’orthographe du hashtag ou du compte ;
- la période sélectionnée ;
- les limites ou quotas de l’API ;
- les logs du service `api` ou du `celery-worker`.

### Les accents sont incorrects dans les PDF

Reconstruire l’image de l’API afin d’installer les polices DejaVu :

```bash
docker compose up -d --build api
```

### Le frontend affiche une ancienne version

```bash
docker compose up -d --build frontend
```

Puis effectuer un rechargement forcé du navigateur avec `Ctrl + F5`.
