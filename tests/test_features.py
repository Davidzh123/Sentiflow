import pytest
from features.preprocessing import clean_tweet, clean_dataframe
import pandas as pd


class TestPreprocessing:
    def test_clean_tweet_urls(self):
        text = "Check this out https://example.com amazing"
        result = clean_tweet(text)
        assert "http" not in result
        assert "example" not in result
    
    def test_clean_tweet_mentions(self):
        text = "Hello @user123 how are you"
        result = clean_tweet(text)
        assert "@" not in result
        assert "user123" not in result
    
    def test_clean_tweet_hashtags(self):
        text = "I love #Python programming"
        result = clean_tweet(text)
        assert "#" not in result
        assert "python" in result
    
    def test_clean_tweet_rt(self):
        text = "RT @user: This is a retweet"
        result = clean_tweet(text)
        assert not result.startswith("rt")
    
    def test_clean_dataframe(self):
        df = pd.DataFrame({
            "text": ["Hello @world https://test.com", "Short", "This is a longer tweet for testing"]
        })
        result = clean_dataframe(df, "text")
        assert "clean_text" in result.columns
        assert len(result) == 2  # "Short" filtré car < 10 chars
