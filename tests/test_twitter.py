"""
Tests for the Twitter API client wrapper.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.twitter import TwitterClient


class TestConnect:
    @patch.dict("os.environ", {}, clear=True)
    @patch("src.twitter.load_dotenv")
    def test_raises_when_all_vars_missing(self, mock_dotenv):
        client = TwitterClient()
        with pytest.raises(EnvironmentError, match="Missing required environment variables"):
            client.connect()

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.twitter.load_dotenv")
    def test_error_lists_missing_var_names(self, mock_dotenv):
        client = TwitterClient()
        with pytest.raises(EnvironmentError) as exc_info:
            client.connect()
        msg = str(exc_info.value)
        for var in ["API_KEY", "API_KEY_SECRET", "ACCESS_TOKEN", "ACCESS_TOKEN_SECRET", "BEARER_TOKEN"]:
            assert var in msg

    @patch.dict(
        "os.environ",
        {"API_KEY": "k", "API_KEY_SECRET": "ks", "ACCESS_TOKEN": "t", "ACCESS_TOKEN_SECRET": "ts"},
        clear=True,
    )
    @patch("src.twitter.load_dotenv")
    def test_error_lists_only_missing_vars(self, mock_dotenv):
        """When only BEARER_TOKEN is missing, only it should be listed."""
        client = TwitterClient()
        with pytest.raises(EnvironmentError) as exc_info:
            client.connect()
        msg = str(exc_info.value)
        assert "BEARER_TOKEN" in msg
        assert "API_KEY," not in msg  # API_KEY is present, shouldn't be listed


class TestPostTweetWithImage:
    def test_raises_when_not_connected(self):
        client = TwitterClient()
        with pytest.raises(RuntimeError, match="Not connected"):
            client.post_tweet_with_image("hello", "/tmp/img.png")

    @patch("src.twitter.tweepy")
    @patch("src.twitter.load_dotenv")
    @patch.dict(
        "os.environ",
        {
            "API_KEY": "k",
            "API_KEY_SECRET": "ks",
            "ACCESS_TOKEN": "t",
            "ACCESS_TOKEN_SECRET": "ts",
            "BEARER_TOKEN": "b",
        },
        clear=True,
    )
    def test_successful_post_flow(self, mock_dotenv, mock_tweepy):
        """Verify that connect + post calls tweepy in the right order."""
        mock_media = MagicMock()
        mock_media.media_id = 12345
        mock_tweepy.API.return_value.media_upload.return_value = mock_media

        client = TwitterClient()
        client.connect()
        client.post_tweet_with_image("test tweet", "/tmp/test.png")

        # Should have uploaded media
        mock_tweepy.API.return_value.media_upload.assert_called_once_with(
            filename="/tmp/test.png"
        )
        # Should have created tweet with media_id
        mock_tweepy.Client.return_value.create_tweet.assert_called_once_with(
            text="test tweet", media_ids=[12345]
        )
