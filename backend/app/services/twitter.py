import math
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from backend.app.config import get_settings

settings = get_settings()


def extract_tweets(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrait les tweets des différents formats renvoyés par TwitterAPI.io."""
    tweets: Any = data.get("tweets", data.get("data", []))
    if isinstance(tweets, dict):
        tweets = tweets.get("tweets", tweets.get("results", []))
    if not isinstance(tweets, list):
        return []
    return [tweet for tweet in tweets if isinstance(tweet, dict)]


def parse_tweet_datetime(tweet_data: dict[str, Any]) -> datetime | None:
    """Retourne une date UTC naive, compatible avec la colonne SQLAlchemy existante."""
    raw_value = (
        tweet_data.get("createdAt")
        or tweet_data.get("created_at")
        or tweet_data.get("tweet_created_at")
        or tweet_data.get("date")
        or tweet_data.get("timestamp")
    )
    if raw_value is None:
        return None

    parsed: datetime | None = None
    if isinstance(raw_value, datetime):
        parsed = raw_value
    elif isinstance(raw_value, (int, float)):
        timestamp = float(raw_value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        parsed = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(raw_value, str):
        value = raw_value.strip()
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None

    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _tweet_id(tweet_data: dict[str, Any]) -> str | None:
    value = tweet_data.get("id") or tweet_data.get("id_str") or tweet_data.get("tweetId")
    return str(value) if value is not None else None


class TwitterService:
    def __init__(self):
        self.api_key = settings.twitter_api_key
        self.base_url = "https://api.twitterapi.io"

    def _headers(self):
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _track_usage():
        try:
            import redis

            r = redis.from_url(get_settings().redis_url)
            r.incr("sentiflow:usage:twitter_calls")
        except Exception:
            pass

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        self._track_usage()
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers(), params=params)

        if response.status_code >= 400:
            return {"error": response.text, "status": response.status_code}
        return response.json()

    @staticmethod
    def _deduplicate(tweets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for tweet in tweets:
            twitter_id = _tweet_id(tweet)
            if not twitter_id or twitter_id in seen_ids:
                continue
            seen_ids.add(twitter_id)
            unique.append(tweet)
        return unique

    async def search_tweets(
        self,
        query: str,
        days: int = 0,
        max_tweets: int = 20,
    ) -> dict[str, Any]:
        """Recherche récente ou historique pour un hashtag/une requête."""
        if not self.api_key:
            return {"error": "TWITTER_API_KEY manquante"}

        max_tweets = max(1, min(int(max_tweets), 1000))
        if days <= 0:
            data = await self._get(
                "/twitter/tweet/advanced_search",
                {"query": query, "queryType": "Latest"},
            )
            if "error" in data:
                return data
            tweets = extract_tweets(data)[:20]
            return {
                "tweets": tweets,
                "raw": data,
                "api_requests": 1,
                "period_days": 0,
                "truncated": False,
            }

        days = max(1, min(int(days), 30))
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        min_window = timedelta(minutes=1)
        max_requests = min(120, max(20, math.ceil(max_tweets / 20) * 6))

        # L'advanced search ne doit pas être paginée. Si une fenêtre remplit
        # la page de 20 tweets, on la coupe en deux jusqu'à obtenir des
        # intervalles assez précis.
        windows = [(start, end)]
        collected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        request_count = 0
        truncated = False

        while windows and len(collected) < max_tweets:
            if request_count >= max_requests:
                truncated = True
                break

            window_start, window_end = windows.pop()
            dated_query = (
                f"{query} since_time:{int(window_start.timestamp())} "
                f"until_time:{int(window_end.timestamp())}"
            )
            data = await self._get(
                "/twitter/tweet/advanced_search",
                {"query": dated_query, "queryType": "Latest"},
            )
            request_count += 1
            if "error" in data:
                return {
                    **data,
                    "api_requests": request_count,
                    "partial_tweets": collected,
                }

            page_tweets = extract_tweets(data)
            if len(page_tweets) >= 12 and window_end - window_start > min_window:
                midpoint = window_start + (window_end - window_start) / 2
                windows.append((window_start, midpoint))
                windows.append((midpoint, window_end))
                continue

            for tweet in page_tweets:
                twitter_id = _tweet_id(tweet)
                if not twitter_id or twitter_id in seen_ids:
                    continue
                seen_ids.add(twitter_id)
                collected.append(tweet)
                if len(collected) >= max_tweets:
                    truncated = bool(windows) or len(page_tweets) >= 20
                    break

        collected.sort(
            key=lambda tweet: parse_tweet_datetime(tweet) or datetime.min,
            reverse=True,
        )
        return {
            "tweets": collected[:max_tweets],
            "raw": {
                "strategy": "adaptive_time_windows",
                "api_requests": request_count,
            },
            "api_requests": request_count,
            "period_days": days,
            "truncated": truncated or bool(windows),
        }

    async def get_user_info(self, username: str):
        """Récupère les infos d'un compte."""
        if not self.api_key:
            return None

        data = await self._get(
            "/twitter/user/info",
            {"userName": username.lstrip("@")},
        )
        return None if "error" in data else data

    async def get_user_tweets(
        self,
        username: str,
        days: int = 0,
        max_tweets: int = 20,
    ) -> dict[str, Any]:
        """Récupère les tweets d'un compte avec pagination par curseur."""
        if not self.api_key:
            return {"error": "TWITTER_API_KEY manquante"}

        username = username.lstrip("@")
        days = max(0, min(int(days), 30))
        max_tweets = max(1, min(int(max_tweets), 1000))
        if days <= 0:
            max_tweets = min(max_tweets, 20)

        cutoff = (
            datetime.utcnow() - timedelta(days=days)
            if days > 0
            else None
        )
        max_pages = min(100, max(1, math.ceil(max_tweets / 20) + 5))
        cursor = ""
        request_count = 0
        collected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        has_next_page = True

        while has_next_page and request_count < max_pages and len(collected) < max_tweets:
            params: dict[str, Any] = {
                "userName": username,
                "includeReplies": False,
            }
            if cursor:
                params["cursor"] = cursor

            data = await self._get("/twitter/user/last_tweets", params)
            request_count += 1
            if "error" in data:
                return {
                    **data,
                    "api_requests": request_count,
                    "partial_tweets": collected,
                }

            page_tweets = extract_tweets(data)
            reached_cutoff = False
            for tweet in page_tweets:
                created_at = parse_tweet_datetime(tweet)
                if cutoff and created_at and created_at < cutoff:
                    reached_cutoff = True
                    continue

                twitter_id = _tweet_id(tweet)
                if not twitter_id or twitter_id in seen_ids:
                    continue
                seen_ids.add(twitter_id)
                collected.append(tweet)
                if len(collected) >= max_tweets:
                    break

            has_next_page = bool(data.get("has_next_page"))
            cursor = str(data.get("next_cursor") or "")
            if reached_cutoff or not cursor or days <= 0:
                has_next_page = False

        collected.sort(
            key=lambda tweet: parse_tweet_datetime(tweet) or datetime.min,
            reverse=True,
        )
        return {
            "tweets": collected[:max_tweets],
            "raw": {
                "strategy": "cursor_pagination",
                "api_requests": request_count,
            },
            "api_requests": request_count,
            "period_days": days,
            "truncated": has_next_page or len(collected) >= max_tweets,
        }

    async def verify_hashtag(self, hashtag: str):
        """Vérifie si un hashtag retourne des tweets."""
        result = await self.search_tweets(hashtag)
        if "error" in result:
            return False
        return len(result.get("tweets", [])) > 0


twitter_service = TwitterService()
