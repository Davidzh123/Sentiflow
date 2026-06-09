import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services.twitter import TwitterService


class TestTwitterService:
    """Tests pour le service Twitter (twitterapi.io)"""
    
    @pytest.fixture
    def twitter_service(self):
        return TwitterService()
    
    @pytest.mark.asyncio
    async def test_search_tweets_success(self, twitter_service):
        """Test recherche de tweets par hashtag"""
        mock_response = {
            "tweets": [
                {"id": "123", "text": "Test tweet #IA", "author": {"userName": "user1"}},
                {"id": "124", "text": "Another tweet #IA", "author": {"userName": "user2"}}
            ]
        }
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.search_tweets("#IA")
            
            assert "tweets" in result
            assert len(result["tweets"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_tweets_error(self, twitter_service):
        """Test erreur lors de la recherche"""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.search_tweets("#IA")
            
            assert "error" in result
            assert result["status"] == 401
    
    @pytest.mark.asyncio
    async def test_get_user_tweets(self, twitter_service):
        """Test récupération des tweets d'un utilisateur"""
        mock_response = {
            "tweets": [
                {"id": "456", "text": "User tweet", "author": {"userName": "elonmusk"}}
            ]
        }
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.get_user_tweets("@elonmusk")
            
            assert "tweets" in result
    
    @pytest.mark.asyncio
    async def test_get_user_tweets_strips_at(self, twitter_service):
        """Test que le @ est bien enlevé du username"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tweets": []}
        
        mock_get = AsyncMock(return_value=mock_resp)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            await twitter_service.get_user_tweets("@testuser")
            
            # Vérifier que le @ a été enlevé dans les params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["userName"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_verify_hashtag_exists(self, twitter_service):
        """Test vérification hashtag existant"""
        mock_response = {
            "tweets": [{"id": "123", "text": "Test"}]
        }
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.verify_hashtag("#Python")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_hashtag_not_exists(self, twitter_service):
        """Test vérification hashtag inexistant"""
        mock_response = {"tweets": []}
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.verify_hashtag("#HashtagQuiExistePas12345")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_user_info_exists(self, twitter_service):
        """Test récupération info utilisateur existant"""
        mock_response = {
            "id": "123",
            "userName": "testuser",
            "name": "Test User"
        }
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.get_user_info("testuser")
            
            assert result is not None
            assert result["userName"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_user_info_not_exists(self, twitter_service):
        """Test récupération info utilisateur inexistant"""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            
            result = await twitter_service.get_user_info("utilisateur_inexistant_12345")
            
            assert result is None
