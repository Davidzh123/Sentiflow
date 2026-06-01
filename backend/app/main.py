import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import engine, Base
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
Base.metadata.create_all(bind=engine)

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


@app.get("/")
def root():
    return {"message": "SentiFlow API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
