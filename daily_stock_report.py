import requests, json, os
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
from stock_info import get_stock_data_today, StockPriceDifference

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

# Function to get stock data from the website
def get_stock_list():
    url = "https://goodinfo.tw/tw2/StockList.asp?RPT_TIME=&MARKET_CAT=智慧選股&INDUSTRY_CAT=外資連買+–+日%40%40外資連續買超%40%40外資連續買超+–+日"

    requestHeaders = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers = requestHeaders)
    response.encoding = 'utf-8'
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table containing the stock data
    table = soup.find('table', {'id': 'tblStockList'})
    headers = [header.text.strip() for header in table.find_all('th')]
    data = []

    for row in table.find_all('tr')[1:]:
        columns = [col.text.strip() for col in row.find_all('td')]
        data.append(columns)

    df = pd.DataFrame(data, columns=headers)
    # Deduplicate the DataFrame based on all columns
    df_deduped_stock_list = df.drop_duplicates(subset=['代號'])
    return df_deduped_stock_list

# Apply the filtering function to the DataFrame with a random delay
def filter_stock_data(row):
    # Introduce a random delay between 3 and 7 seconds
    delay_seconds = random.uniform(3, 7)
    time.sleep(delay_seconds)

    stock_number = row['代號']
    n_records = 9  # Default value
    desired_min_percent = -20.0  # Default value
    desired_max_percent = 5.0  # Default value

    # Call get_stock_data_today function
    stock_data = get_stock_data_today(stock_number, n_records)

    if stock_data is None:
        logger.info(f"No stock data for: {stock_number}")
        return False # Remove the record
    
    if stock_data.percentage_difference is None:
        logger.info(f"stock_data.percentage_difference is none: {stock_number}")
        return False  # Remove the record

    # Check if percentage_difference is within the desired range
    if not (desired_min_percent <= stock_data.percentage_difference <= desired_max_percent):
        logger.info(f"stock_data.percentage_difference is not in range: {stock_number}")
        return False # Remove the record

    return True


try:
    # Check if today is a trading day
    if not is_trading_day():
        logger.info("Today is not a trading day. Skipping main process.")
        exit()
except Exception as e:
    logger.error(f"Error: {e}")
    exit()

logger.info("Starting stock report process...")

# Find the path of the current script
script_path = os.path.dirname(os.path.abspath(__file__))
# Construct the path to config.json
config_path = os.path.join(script_path, 'config.json')
# Read the properties file
properties = read_properties(config_path)

# Get initial stock data
stock_list = get_stock_list()

# Check if the table is found
if stock_list is not None:
    # Read min_cont_buy_days from the properties file with a default value of 5
    min_cont_buy_days = properties.get('min_cont_buy_days', 5)
    discord_webhook_url = properties.get('discord_webhook_url', '')

    # Convert the column to numeric for comparison
    stock_list['外資連續買賣日數'] = pd.to_numeric(stock_list['外資連續買賣日數'], errors='coerce')

    # Filter DataFrame records where "外資連續買賣日數" is smaller than min_cont_buy_days
    df_day_filtered = stock_list[stock_list['外資連續買賣日數'] >= min_cont_buy_days]

    # Apply the filtering function to the DataFrame
    hp_stock_data = df_day_filtered[df_day_filtered.apply(filter_stock_data, axis=1)]

    # Save the filtered DataFrame to a CSV file with "big5" encoding
    hp_stock_data.to_csv('hp_stock_data.csv', index=False, encoding='big5', errors='replace')

    # Create a message for the Discord webhook
    message = f"外資連續{min_cont_buy_days}日以上買超, 10日漲跌幅區間:-20% ~ 5%"

    # Create a file object from the CSV file
    file = {'file': ('hp_stock_data.csv', open('hp_stock_data.csv', 'rb'))}

    # Include the message in the Discord webhook request
    payload = {
        'content': message
    }

    # Make a POST request to the Discord webhook with the file and message attached
    response_discord = requests.post(discord_webhook_url, data=payload, files=file)

    # Check if the Discord webhook request was successful
    if response_discord.status_code == 200:
        logger.info("Deduplicated and filtered data sent to Discord webhook successfully.")
    else:
        logger.error(f"Failed to send deduplicated and filtered data to Discord webhook. Status Code: {response_discord.status_code}")
else:
    logger.error("Table not found on the page.")
