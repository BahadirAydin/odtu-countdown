"""
Twitter API connection and posting utilities.
"""

import logging
import os

try:
    import tweepy
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    tweepy = None
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class TwitterClient:
    """Wrapper around Tweepy for Twitter API v1.1 and v2."""

    def __init__(self):
        self._client = None
        self._api = None

    def connect(self) -> None:
        """
        Connect to the Twitter API using environment variables.

        Required env vars: API_KEY, API_KEY_SECRET, ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET, BEARER_TOKEN
        """
        load_dotenv()

        api_key = os.getenv("API_KEY")
        api_key_secret = os.getenv("API_KEY_SECRET")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
        bearer_token = os.getenv("BEARER_TOKEN")

        missing = []
        if not api_key:
            missing.append("API_KEY")
        if not api_key_secret:
            missing.append("API_KEY_SECRET")
        if not access_token:
            missing.append("ACCESS_TOKEN")
        if not access_token_secret:
            missing.append("ACCESS_TOKEN_SECRET")
        if not bearer_token:
            missing.append("BEARER_TOKEN")

        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        if tweepy is None:
            raise ModuleNotFoundError(
                "tweepy is required to connect to Twitter API. Install dependencies first."
            )

        auth = tweepy.OAuth1UserHandler(
            api_key, api_key_secret, access_token, access_token_secret
        )
        self._api = tweepy.API(auth)
        self._client = tweepy.Client(
            bearer_token, api_key, api_key_secret, access_token, access_token_secret
        )
        logger.info("Connected to Twitter API")

    def post_tweet_with_image(self, text: str, image_path: str) -> None:
        """
        Upload an image and post a tweet with it.

        Args:
            text: Tweet text content.
            image_path: Path to the image file to attach.
        """
        if self._api is None or self._client is None:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            media = self._api.media_upload(filename=image_path)
            self._client.create_tweet(text=text, media_ids=[media.media_id])
            logger.info("Successfully posted tweet with image")
        except Exception as e:
            logger.error("Failed to post tweet: %s", e)
            raise
