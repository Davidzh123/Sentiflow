from backend.app.routes.auth import router as auth_router
from backend.app.routes.targets import router as targets_router
from backend.app.routes.tweets import router as tweets_router
from backend.app.routes.analysis import router as analysis_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.twitter import router as twitter_router
from backend.app.routes.admin import router as admin_router

__all__ = ["auth_router", "targets_router", "tweets_router", "analysis_router", "alerts_router", "twitter_router", "admin_router"]
