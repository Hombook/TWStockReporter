import os
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed

from logger_config import setup_logger

# Set up the logger
logger = setup_logger()

# Function to check if today is a trading day
def is_trading_day():
    today_date = datetime.now().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={today_date}&type=MS&response=csv"
    response = requests.get(url)
    return bool(response.text.strip())  # If the response is empty, it's not a trading day

# Function to read properties from a JSON file
def read_properties(file_path):
    with open(file_path, 'r') as file:
        properties = json.load(file)
    return properties

# Function to fetch CSV data from the given URL
def fetch_csv_data(url):
    response = requests.get(url)
    return response.text

# Function to send CSV data as a file and message to Discord webhook
def send_to_discord_webhook(webhook_url, csv_data, filename, message):
    # Encode CSV data to Big5
    csv_data_big5 = csv_data.encode('big5', errors='ignore')

    webhook = DiscordWebhook(url=webhook_url, content=message)
    webhook.add_file(file=csv_data_big5, filename=filename)
    webhook.execute()

if __name__ == "__main__":
    try:
        # Check if today is a trading day
        if not is_trading_day():
            logger.info("Today is not a trading day. Skipping main process.")
            exit()
    except Exception as e:
        logger.error(f"Error: {e}")
        exit()

    # Find the path of the current script
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to config.json
    config_path = os.path.join(script_path, 'config.json')
    # Read the properties file
    properties = read_properties(config_path)

    # Get today's date in the format YYYYMMDD
    today_date = datetime.now().strftime("%Y%m%d")

    # Replace this URL with the actual URL you want to fetch data from
    twse_3insti_url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today_date}&selectType=ALL&response=csv"
    tpex_3insti_url = "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=csv&se=EW&t=D"

    try:
        # Read Discord webhook URL from config.json
        discord_webhook_url = properties.get('discord_webhook_url', '')

        if not discord_webhook_url:
            raise ValueError("Discord webhook URL not found in config.json")

         # Get today's date in the format YYYYMMDD
        today_date_readable = datetime.now().strftime("%Y年%m月%d日")

        # Fetch TWSE data
        twse_csv_data = fetch_csv_data(twse_3insti_url)
        # Send TWSE data to Discord webhook
        send_to_discord_webhook(discord_webhook_url, twse_csv_data, f"twse_3insti_{today_date}.csv", f"{today_date_readable} 證交所-三大法人買賣超日報")

        # Fetch TPEX data
        tpex_csv_data = fetch_csv_data(tpex_3insti_url)
        # Send TPEX data to Discord webhook
        send_to_discord_webhook(discord_webhook_url, tpex_csv_data, f"tpex_3insti_{today_date}.csv", f"{today_date_readable} 櫃買中心-三大法人買賣超日報")

        logger.info("CSV data sent to Discord successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
