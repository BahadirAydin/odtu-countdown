import os
import schedule
import time
from datetime import datetime
import tweepy
import logging
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from os import environ

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def calculate_percentage(start_date, end_date):
    """Calculate the percentage of time elapsed between start and end dates."""
    total = (end_date - start_date).total_seconds()
    elapsed = (datetime.now() - start_date).total_seconds()
    if elapsed > total:
        return 100
    return round((elapsed / total) * 100, 2)


def create_progress_image(percentage, width=800, height=200):
    """Create a polished progress bar image using matplotlib."""
    fig, ax = plt.subplots(figsize=(width / 100, height / 100))

    # Main progress bar
    bar_color = "#ff7f7f"
    ax.barh([0], [percentage], color=bar_color, height=0.3, edgecolor="none", left=0)

    # Add background for remaining progress
    remaining_color = "#fff"  # Light grey for remaining
    ax.barh(
        [0],
        [100 - percentage],
        left=[percentage],
        color=remaining_color,
        height=0.3,
        edgecolor="none",
    )

    # Center text for percentage
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
    img_path = "progress_image.png"
    plt.savefig(img_path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    logging.info(f"Image successfully saved to {img_path}")
    return img_path


def connect_twitter():
    """Connect to the Twitter API using Tweepy and environment variables."""
    load_dotenv()
    tweepy_auth = tweepy.OAuth1UserHandler(
        environ["API_KEY"],
        environ["API_KEY_SECRET"],
        environ["ACCESS_TOKEN"],
        environ["ACCESS_TOKEN_SECRET"],
    )
    client = tweepy.Client(
        environ["BEARER_TOKEN"],
        environ["API_KEY"],
        environ["API_KEY_SECRET"],
        environ["ACCESS_TOKEN"],
        environ["ACCESS_TOKEN_SECRET"],
    )
    api = tweepy.API(tweepy_auth)
    return client, api


def post_photo():
    """Generate and post a progress image on Twitter."""
    client, api = connect_twitter()
    start_date = datetime(2024, 9, 30)
    end_date = datetime(2025, 1, 3)
    remaining_days = (end_date - datetime.now()).days
    percentage = calculate_percentage(start_date, end_date)
    img_path = create_progress_image(percentage)
    text = f"🔴 ODTÜ'de 2024-2025 güz dönemi ilerlemesi: %{percentage} "
    text += f"\n🗓️ Kalan gün sayısı: {remaining_days}"
    media = api.media_upload(filename=img_path)
    client.create_tweet(text=text, media_ids=[media.media_id])
    logging.info("Posted image")


def retry_scheduled_task(task, max_retries=3, retry_delay=300):
    """Retry a scheduled task if it fails."""
    attempts = 0
    while attempts < max_retries:
        try:
            task()
            logging.info("Task completed successfully.")
            break
        except Exception as e:
            attempts += 1
            logging.error(f"Task failed: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)


schedule.every().day.at("10:40").do(retry_scheduled_task, task=post_photo)
schedule.every().day.at("17:30").do(retry_scheduled_task, task=post_photo)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(30)
