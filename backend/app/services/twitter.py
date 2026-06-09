import httpx
from typing import Optional
from backend.app.config import get_settings

settings = get_settings()

API_BASE_URL = "https://api.twitterapi.io/twitter"


class TwitterService:
    """Service pour interagir avec twitterapi.io"""
    
    def __init__(self):
        self.api_key = settings.twitter_api_key
        self.headers = {"X-API-Key": self.api_key}
    
    async def search_tweets(self, query: str, limit: int = 20) -> dict:
        """Recherche des tweets par hashtag ou mot-clé"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/tweet/advanced_search",
                headers=self.headers,
                params={
                    "query": query,
                    "queryType": "Latest"
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {"error": response.text, "status": response.status_code}
    
    async def get_user_tweets(self, username: str, limit: int = 20) -> dict:
        """Récupère les derniers tweets d'un utilisateur"""
        # Enlever le @ si présent
        username = username.lstrip("@")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/user/last_tweets",
                headers=self.headers,
                params={"userName": username},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return {"error": response.text, "status": response.status_code}
    
    async def get_user_info(self, username: str) -> Optional[dict]:
        """Vérifie si un utilisateur existe et retourne ses infos"""
        username = username.lstrip("@")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/user/info",
                headers=self.headers,
                params={"userName": username},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    async def verify_hashtag(self, hashtag: str) -> bool:
        """Vérifie si un hashtag a des tweets récents"""
        hashtag = hashtag.lstrip("#")
        result = await self.search_tweets(f"#{hashtag}")
        
        if "error" in result:
            return False
        
        tweets = result.get("tweets", result.get("data", []))
        return len(tweets) > 0


twitter_service = TwitterService()
