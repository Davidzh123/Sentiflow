<<<<<<< HEAD
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.database import engine, Base
from backend.app.routes import auth_router, targets_router, tweets_router, analysis_router, alerts_router, twitter_router, admin_router, tasks_router
from backend.app.routes.rag import router as rag_router
from backend.app.routes.monitoring import router as monitoring_router
from backend.app.routes.mlflow_routes import router as mlflow_router
from backend.app.routes.data_export import router as data_export_router

# Configuration du logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("sentiflow")

settings = get_settings()

# Activer pgvector
from sqlalchemy import text as sql_text
with engine.connect() as conn:
    conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="API d'analyse de sentiments Twitter",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(targets_router)
app.include_router(tweets_router)
app.include_router(analysis_router)
app.include_router(alerts_router)
app.include_router(twitter_router)
app.include_router(admin_router)
app.include_router(tasks_router)
app.include_router(rag_router)
app.include_router(monitoring_router)
app.include_router(mlflow_router)
app.include_router(data_export_router)


@app.get("/")
def root():
    return {"message": "SentiFlow API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
=======
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import engine, Base
from backend.app.services.demo_schema_migrations import run_demo_schema_migrations
from backend.app.routes import (
    auth_router,
    targets_router,
    tweets_router,
    analysis_router,
    alerts_router,
    twitter_router,
    admin_router,
    tasks_router,
    llm_router,
    dashboards_router,
    feedback_router,
)

# Configuration du logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentiflow")

settings = get_settings()

# Créer les tables au démarrage pour le mode projet/demo.
# create_all crée les tables manquantes, mais ne modifie pas les tables déjà existantes.
# Les petites migrations ci-dessous évitent de supprimer le volume Postgres après un patch.
Base.metadata.create_all(bind=engine)
run_demo_schema_migrations(engine)

app = FastAPI(
    title=settings.app_name,
    description="API d'analyse de sentiments Twitter avec agent LLM SentiFlow",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(targets_router)
app.include_router(tweets_router)
app.include_router(analysis_router)
app.include_router(alerts_router)
app.include_router(twitter_router)
app.include_router(admin_router)
app.include_router(tasks_router)
app.include_router(llm_router)
app.include_router(dashboards_router)
app.include_router(feedback_router)


@app.get("/")
def root():
    return {"message": "SentiFlow API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
>>>>>>> de7e700a57fde813194d5d256df032c07dda626c
