import os
import schedule
import time
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import tweepy

# Configuration
START_DATE = datetime(2024, 9, 30)
END_DATE = datetime(2025, 1, 3)
IMAGE_PATH = "progress_image.png"
POLLING_INTERVAL = 30  # in seconds
RETRY_DELAY = 300  # in seconds
MAX_RETRIES = 3

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def calculate_percentage(start_date: datetime, end_date: datetime) -> float:
    """
    Calculate the percentage of time elapsed between the start and end dates.

    Args:
        start_date (datetime): The starting date.
        end_date (datetime): The ending date.

    Returns:
        float: The percentage of elapsed time.
    """
    total_seconds = (end_date - start_date).total_seconds()
    elapsed_seconds = (datetime.now() - start_date).total_seconds()
    percentage = (
        (elapsed_seconds / total_seconds) * 100
        if elapsed_seconds < total_seconds
        else 100
    )
    return round(percentage, 2)


def create_progress_image(
    percentage: float, width: int = 800, height: int = 200
) -> str:
    """
    Create a progress bar image using matplotlib and save it.

    Args:
        percentage (float): The progress percentage to display.
        width (int): Width of the progress bar image (default: 800).
        height (int): Height of the progress bar image (default: 200).

    Returns:
        str: The file path of the saved image.
    """
    fig, ax = plt.subplots(figsize=(width / 100, height / 100))

    # Main progress bar
    ax.barh([0], [percentage], color="#ff7f7f", height=0.3, edgecolor="none", left=0)
    ax.barh(
        [0],
        [100 - percentage],
        color="#fff",
        height=0.3,
        edgecolor="none",
        left=percentage,
    )

    # Center text
    ax.text(
        50,
        0,
        f"{percentage}%",
        va="center",
        ha="center",
        fontsize=24,
        color="black",
        weight="bold",
    )

    # Remove axes and ticks
    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_frame_on(False)

    # Save the image
    plt.savefig(IMAGE_PATH, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    logging.info(f"Image successfully saved to {IMAGE_PATH}")
    return IMAGE_PATH


def connect_twitter() -> tuple:
    """
    Connect to the Twitter API using Tweepy and environment variables.

    Returns:
        tuple: A tuple containing the Twitter client and API instances.
    """
    load_dotenv()
    tweepy_auth = tweepy.OAuth1UserHandler(
        os.getenv("API_KEY"),
        os.getenv("API_KEY_SECRET"),
        os.getenv("ACCESS_TOKEN"),
        os.getenv("ACCESS_TOKEN_SECRET"),
    )
    api = tweepy.API(tweepy_auth)
    client = tweepy.Client(
        os.getenv("BEARER_TOKEN"),
        os.getenv("API_KEY"),
        os.getenv("API_KEY_SECRET"),
        os.getenv("ACCESS_TOKEN"),
        os.getenv("ACCESS_TOKEN_SECRET"),
    )
    logging.info("Connected to Twitter API")
    return client, api


def post_photo():
    """
    Generate and post a progress image on Twitter with the remaining days and progress.
    """
    client, api = connect_twitter()
    remaining_days = (END_DATE - datetime.now()).days
    percentage = calculate_percentage(START_DATE, END_DATE)
    img_path = create_progress_image(percentage)

    text = f"🔴 ODTÜ'de 2024-2025 güz dönemi ilerlemesi: %{percentage} \n🗓️ Kalan gün sayısı: {remaining_days}"
    media = api.media_upload(filename=img_path)
    client.create_tweet(text=text, media_ids=[media.media_id])
    logging.info("Successfully posted progress image on Twitter")


def retry(max_retries: int = MAX_RETRIES, retry_delay: int = RETRY_DELAY):
    """
    Decorator to retry a task on failure.

    Args:
        max_retries (int): Maximum number of retries (default: 3).
        retry_delay (int): Delay between retries in seconds (default: 300).
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    result = func(*args, **kwargs)
                    logging.info("Task completed successfully.")
                    return result
                except Exception as e:
                    attempts += 1
                    logging.error(
                        f"Task failed: {e}. Retrying {attempts}/{max_retries} in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
            logging.error("Max retries reached. Task failed permanently.")

        return wrapper

    return decorator


@retry()
def scheduled_post_photo():
    """A wrapper around the post_photo function to be used for scheduling with retries."""
    post_photo()


def schedule_tasks():
    """
    Schedule tasks to post the progress photo at specified times.
    """
    schedule.every().day.at("10:40").do(scheduled_post_photo)
    schedule.every().day.at("17:30").do(scheduled_post_photo)
    logging.info("Scheduled tasks successfully")


if __name__ == "__main__":
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(POLLING_INTERVAL)
