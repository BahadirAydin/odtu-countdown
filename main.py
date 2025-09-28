import os
import time
import logging
import argparse
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import tweepy

# Set timezone
os.environ["TZ"] = "Europe/Istanbul"
time.tzset()

# Configuration
START_DATE = datetime(2025, 9, 29)
END_DATE = datetime(2026, 1, 3)
IMAGE_PATH = "progress_image.png"
PROGRESS_TEXT = "⚪ 2025-2026 güz dönemi ilerlemesi"

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def is_more_than_a_day_before(
    start_date: datetime, now: datetime | None = None
) -> bool:
    """
    Return True if 'now' is more than 24 hours earlier than 'start_date'.
    """
    now = now or datetime.now()
    return now < (start_date - timedelta(days=1))


def calculate_percentage(start_date: datetime, end_date: datetime) -> float | int:
    """
    Calculate the percentage of time elapsed between the start and end dates.

    Args:
        start_date (datetime): The starting date.
        end_date (datetime): The ending date.

    Returns:
        float | int: The percentage of elapsed time, as int if no decimal part.
    """
    now = datetime.now()
    if now < start_date:
        return 0
    elif now.date() == (end_date - timedelta(days=1)).date():
        return 100

    total_seconds = (end_date - start_date).total_seconds()
    elapsed_seconds = (now - start_date).total_seconds()
    percentage = round((elapsed_seconds / total_seconds) * 100, 2)

    return int(percentage) if percentage.is_integer() else percentage


def create_progress_image(
    percentage: float | int, width: int = 800, height: int = 200
) -> str:
    """
    Create a progress bar image using matplotlib and save it.

    Args:
        percentage (float | int): The progress percentage to display.
        width (int): Width of the progress bar image (default: 800).
        height (int): Height of the progress bar image (default: 200).

    Returns:
        str: The file path of the saved image.
    """
    fig, ax = plt.subplots(figsize=(width / 100, height / 100))

    # Main progress bar
    ax.barh([0], [percentage], color="#86feff", height=0.3, edgecolor="none", left=0)
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
    plt.savefig(IMAGE_PATH, bbox_inches="tight", pad_inches=0.05)
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
    Skips posting if now is more than 1 day before START_DATE.
    """
    # Early guard: do not tweet if it's more than a day before the start date
    if is_more_than_a_day_before(START_DATE):
        logging.info(
            "Skipping tweet: More than 1 day remains before START_DATE (%s).",
            START_DATE,
        )
        return

    client, api = connect_twitter()
    percentage = calculate_percentage(START_DATE, END_DATE)
    img_path = create_progress_image(percentage)

    text = f"{PROGRESS_TEXT}: %{percentage}"
    media = api.media_upload(filename=img_path)
    client.create_tweet(text=text, media_ids=[media.media_id])
    logging.info("Successfully posted progress image on Twitter")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Post semester progress on Twitter or view percentage."
    )
    parser.add_argument(
        "--percentage-only",
        action="store_true",
        help="Only show the current percentage and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run everything except actually posting to Twitter.",
    )
    args = parser.parse_args()

    percentage = calculate_percentage(START_DATE, END_DATE)

    if args.percentage_only:
        print(f"{PROGRESS_TEXT}: %{percentage}")
    else:
        early = is_more_than_a_day_before(START_DATE)
        if early:
            logging.info(
                "More than 1 day before START_DATE (%s). Tweet will be skipped.",
                START_DATE,
            )

        client, api = connect_twitter()
        logging.info(f"Dry run: {args.dry_run}")
        img_path = create_progress_image(percentage)
        text = f"{PROGRESS_TEXT}: %{percentage}"

        if args.dry_run:
            if early:
                logging.info(
                    "Dry run mode: Would NOT post due to early guard. Content would have been:"
                )
            else:
                logging.info(
                    "Dry run mode: Image would be posted with the following content:"
                )
            logging.info(f"Text: {text}")
            logging.info(f"Image path: {img_path}")
        else:
            if early:
                logging.info("Skipping actual tweet due to early guard.")
            else:
                media = api.media_upload(filename=img_path)
                client.create_tweet(text=text, media_ids=[media.media_id])
                logging.info("Successfully posted progress image on Twitter")

