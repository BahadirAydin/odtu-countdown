import tweepy
import os
import schedule
import time
from datetime import datetime
import urllib.parse
import requests
import logging
from dotenv import load_dotenv
from os import listdir, environ

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_percentage(start_date, end_date):
    total_hours = (end_date - start_date).total_seconds() / 3600  # Convert seconds to hours
    elapsed_hours = (datetime.now() - start_date).total_seconds() / 3600
    if elapsed_hours > total_hours:
        return 100
    return round((elapsed_hours / total_hours) * 100, 2)

def make_request(url, headers):
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            else:
                logging.warning(f"Failed to download the image, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}, retrying...")
            retry_count += 1
            time.sleep(5)  # Wait for 5 seconds before retrying
    return None

def create_progress_image(percentage, width=800, height=200):
    remaining_percentage = 100 - percentage
    label_text = urllib.parse.quote(f"{percentage}%")
    chart_url = f"https://image-charts.com/chart?chbr=5&chco=e31836%2Cffffff&chd=a:{int(percentage)}|{int(remaining_percentage)}&chl={label_text}&chdlp=b&chlps=font.size%2C30%7Ccolor%2C000000&chf=bg%2Cs%2C020e1a&chma=20%2C20%2C25%2C25&chof=png&chs={width}x{height}&cht=bhs&chxs=0%2CFFFFFF00%2C0%2C-1%2C_%2CFFFFFF00%2CFFFFFF00%7C1%2CFFFFFF00%2C0%2C-1%2C_%2CFFFFFF00%2CFFFFFF00&chxt=x%2Cy"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
        'Accept': 'image/avif,image/webp,*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://image-charts.com/',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }

    response = make_request(chart_url, headers)
    img_path = 'progress_image.png'
    if response:
        with open(img_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"Image successfully saved to {img_path}")
    else:
        logging.error("Failed to download the image after multiple attempts")
    return img_path

# Load environment variables

def connect_twitter():
    load_dotenv()
    tweepy_auth = tweepy.OAuth1UserHandler(environ['API_KEY'], environ['API_KEY_SECRET'], environ['ACCESS_TOKEN'], environ['ACCESS_TOKEN_SECRET'])
    client = tweepy.Client(environ['BEARER_TOKEN'], environ['API_KEY'], environ['API_KEY_SECRET'], environ['ACCESS_TOKEN'], environ['ACCESS_TOKEN_SECRET'])
    api = tweepy.API(tweepy_auth)
    return client, api

def post_photo():
    client, api = connect_twitter()
    start_date = datetime(2024, 2, 19)
    end_date = datetime(2024, 6, 15)
    percentage = calculate_percentage(start_date, end_date)
    img_path = create_progress_image(percentage)
    text = f"ODTÜ'de bahar dönemi ilerlemesi: %{percentage}"
    media = api.media_upload(filename=img_path)
    client.create_tweet(text=text, media_ids=[media.media_id])
    logging.info("Posted image")

def post_remaining_days():
    client, api = connect_twitter()
    remaining_days = (datetime(2024, 6, 15) - datetime.now()).days
    img_path = create_remaining_days_image(remaining_days)
    text = f"ODTÜ'de bahar döneminin bitmesine kalan gün sayısı: {remaining_days}"
    media = api.media_upload(filename=img_path)
    client.create_tweet(text=text, media_ids=[media.media_id])
    logging.info("Posted image")

# Schedule to post every 3 hours
schedule.every().day.at("01:00").do(post_photo)
schedule.every().day.at("04:00").do(post_photo)
schedule.every().day.at("07:00").do(post_photo)
schedule.every().day.at("10:00").do(post_photo)
schedule.every().day.at("13:00").do(post_photo)
schedule.every().day.at("16:00").do(post_photo)
schedule.every().day.at("19:00").do(post_photo)
schedule.every().day.at("22:00").do(post_photo)
schedule.every().day.at("19:00").do(post_remaining_days)

while True:
    schedule.run_pending()
    time.sleep(30)
