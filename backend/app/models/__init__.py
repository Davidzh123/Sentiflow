<<<<<<< HEAD
from backend.app.models.user import User
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet
from backend.app.models.alert import Alert
from backend.app.models.account import Account
from backend.app.models.sentiment_aggregate import SentimentAggregate
from backend.app.models.dashboard import Dashboard, DashboardExport
from backend.app.models.feedback import Feedback
try:
    from backend.app.models.embedding import TweetEmbedding
except ImportError:
    TweetEmbedding = None  # pgvector non installé — RAG from scratch utilisé
from backend.app.models.prediction_log import PredictionLog
from backend.app.models.drift_log import DriftLog

__all__ = [
    "User", "Target", "Tweet", "Alert",
    "Account", "SentimentAggregate",
    "Dashboard", "DashboardExport", "Feedback",
    "TweetEmbedding", "PredictionLog", "DriftLog"
]
=======
from backend.app.models.user import User
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet
from backend.app.models.alert import Alert
from backend.app.models.account import Account
from backend.app.models.sentiment_aggregate import SentimentAggregate
from backend.app.models.dashboard import Dashboard, DashboardExport
from backend.app.models.feedback import Feedback
from backend.app.models.generated_dashboard import GeneratedDashboard
from backend.app.models.llm_feedback import LLMFeedback

__all__ = [
    "User", "Target", "Tweet", "Alert",
    "Account", "SentimentAggregate",
    "Dashboard", "DashboardExport", "Feedback", "GeneratedDashboard", "LLMFeedback"
]
>>>>>>> de7e700a57fde813194d5d256df032c07dda626c
