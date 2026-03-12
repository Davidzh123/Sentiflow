from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.database import engine, Base
from backend.app.routes import auth_router, targets_router, tweets_router, analysis_router, alerts_router, twitter_router, admin_router

settings = get_settings()

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


@app.get("/")
def root():
    return {"message": "SentiFlow API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
