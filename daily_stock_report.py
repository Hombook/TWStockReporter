import requests
import pandas as pd
from bs4 import BeautifulSoup
import json

# Read Discord webhook URL and min_cont_buy_days from config.json
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)
    discord_webhook_url = config_data.get('discord_webhook_url', '')
    min_cont_buy_days = config_data.get('min_cont_buy_days', 5)

# URL of the website
url = "https://goodinfo.tw/tw2/StockList.asp?RPT_TIME=&MARKET_CAT=智慧選股&INDUSTRY_CAT=外資連買+–+日%40%40外資連續買超%40%40外資連續買超+–+日"

# Header for mimicking a web browser
requestHeaders = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

# Send a GET request to the URL
response = requests.get(url, headers = requestHeaders)
response.encoding = 'utf-8'

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table containing the stock data
    table = soup.find('table', {'id': 'tblStockList'})

    # Check if the table is found
    if table:
        # Extract the headers of the table
        headers = [header.text.strip() for header in table.find_all('th')]

        # Extract the rows of the table
        rows = []
        for row in table.find_all('tr')[1:]:
            row_data = [data.text.strip() for data in row.find_all('td')]
            rows.append(row_data)

        # Create a pandas DataFrame from the extracted data
        df = pd.DataFrame(rows, columns=headers)

        # Deduplicate DataFrame based on certain columns (e.g., '代號' in this case)
        df_deduped = df.drop_duplicates(subset=['代號'])

        # Convert the column to numeric for comparison
        df_deduped['外資連續買賣日數'] = pd.to_numeric(df_deduped['外資連續買賣日數'], errors='coerce')

        # Filter DataFrame records where "外資連續買賣日數" is smaller than min_cont_buy_days
        df_filtered = df_deduped[df_deduped['外資連續買賣日數'] >= min_cont_buy_days]

        # Save the filtered DataFrame to a CSV file with ASCII encoding
        df_filtered.to_csv('filtered_stock_data.csv', index=False, encoding='big5', errors='replace')

        # Create a file object from the CSV file
        file = {'file': ('filtered_stock_data.csv', open('filtered_stock_data.csv', 'rb'))}

        # Include a message in the Discord webhook request
        message = f"外資連續{min_cont_buy_days}日以上買超資料"

        # Make a POST request to the Discord webhook with the file and message attached
        response_discord = requests.post(discord_webhook_url, files=file, data={'content': message})

        # Check if the Discord webhook request was successful
        if response_discord.status_code == 200:
            print("Deduplicated and filtered data sent to Discord webhook successfully.")
        else:
            print(f"Failed to send deduplicated and filtered data to Discord webhook. Status Code: {response_discord.status_code}")
    else:
        print("Table not found on the page.")
else:
    print(f"Failed to retrieve data. Status Code: {response.status_code}")
