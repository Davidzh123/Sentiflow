from celery import Celery
from backend.app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sentiflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Planification des tâches périodiques (Celery Beat)
celery_app.conf.beat_schedule = {
    # Collecte auto toutes les 2 minutes (TEST)
    "collect-all-targets": {
        "task": "backend.app.tasks.collect_all_targets",
        "schedule": 120.0,  # 2 min
    },
    # Analyse auto toutes les 3 minutes (TEST)
    "analyze-all-targets": {
        "task": "backend.app.tasks.analyze_all_targets",
        "schedule": 180.0,  # 3 min
    },
    # Vérifier les alertes toutes les 4 minutes (TEST)
    "check-alerts": {
        "task": "backend.app.tasks.check_all_alerts",
        "schedule": 240.0,  # 4 min
    },
    # Agréger les sentiments toutes les 5 minutes (TEST)
    "aggregate-sentiments": {
        "task": "backend.app.tasks.aggregate_sentiments",
        "schedule": 300.0,  # 5 min
    },
}
