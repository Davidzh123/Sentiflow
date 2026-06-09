<<<<<<< HEAD
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
=======
import httpx

from backend.app.config import get_settings


settings = get_settings()


class TwitterService:
    def __init__(self):
        self.api_key = settings.twitter_api_key
        self.base_url = "https://api.twitterapi.io"

    def _headers(self):
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def search_tweets(self, query: str):
        """
        Recherche des tweets pour un hashtag ou une requête.
        """
        if not self.api_key:
            return {"error": "TWITTER_API_KEY manquante"}

        url = f"{self.base_url}/twitter/tweet/advanced_search"

        params = {
            "query": query,
            "queryType": "Latest",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers(), params=params)

        if response.status_code >= 400:
            return {
                "error": response.text,
                "status": response.status_code,
            }

        data = response.json()

        return {
            "tweets": data.get("tweets", data.get("data", [])),
            "raw": data,
        }

    async def get_user_info(self, username: str):
        """
        Récupère les infos d'un compte.
        """
        if not self.api_key:
            return None

        username = username.lstrip("@")
        url = f"{self.base_url}/twitter/user/info"

        params = {
            "userName": username,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers(), params=params)

        if response.status_code >= 400:
            return None

        return response.json()

    async def get_user_tweets(self, username: str):
        """
        Récupère les tweets d'un compte.
        """
        if not self.api_key:
            return {"error": "TWITTER_API_KEY manquante"}

        username = username.lstrip("@")
        url = f"{self.base_url}/twitter/user/last_tweets"

        params = {
            "userName": username,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers(), params=params)

        if response.status_code >= 400:
            return {
                "error": response.text,
                "status": response.status_code,
            }

        data = response.json()

        return {
            "tweets": data.get("tweets", data.get("data", [])),
            "raw": data,
        }

    async def verify_hashtag(self, hashtag: str):
        """
        Vérifie rapidement si un hashtag retourne des tweets.
        """
        result = await self.search_tweets(hashtag)

        if "error" in result:
            return False

        tweets = result.get("tweets", [])

        return isinstance(tweets, list) and len(tweets) > 0


twitter_service = TwitterService()
>>>>>>> de7e700a57fde813194d5d256df032c07dda626c
