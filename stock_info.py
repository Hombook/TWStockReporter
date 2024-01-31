import requests
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from logger_config import setup_logger

# Set up the logger
logger = setup_logger()

class StockPriceDifference:
    def __init__(self, price_difference, percentage_difference, input_date_closing_price, earlier_closing_price):
        self.price_difference = price_difference
        self.percentage_difference = percentage_difference
        self.input_date_closing_price = input_date_closing_price
        self.earlier_closing_price = earlier_closing_price

def fetch_data(url):
    logger.debug(f"Fetching: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.HTTPError as errh:
        logger.error(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logger.error(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        logger.error(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Error: {err}")
    return None

def get_stock_price_difference(stock_number, date_time, n_records):
    # Parse input date_time to extract the first day of the month
    input_date = datetime.strptime(date_time, '%Y%m%d')
    first_day_of_month = input_date.replace(day=1)

    # Format the first day of the month for the URL
    formatted_date = first_day_of_month.strftime('%Y%m%d')

    # Construct the URL for fetching data
    url = f'https://www.twse.com.tw/rwd/en/afterTrading/STOCK_DAY?date={formatted_date}&stockNo={stock_number}&response=json'

    # Make the request and parse the JSON response
    data = fetch_data(url)

    # Check if the request was successful
    if data.get('stat') == 'OK':
        # Extract the fields and data from the response
        fields = data['fields']
        stock_data = data['data']

        # Find the index of the 'Closing Price' field
        closing_price_index = fields.index('Closing Price')

        # Find the index of the input date in the data
        input_date_index = next((i for i, record in enumerate(stock_data) if record[0] == input_date.strftime('%Y/%m/%d')), None)

        if input_date_index is not None:
            input_date_index = input_date_index
            # Get the Closing Price for the input date
            input_date_closing_price = float(stock_data[input_date_index][closing_price_index].replace(',', ''))

            # Find the index of the earlier record based on n_records
            earlier_index = input_date_index - n_records

            # Check if there are enough earlier records in the current list
            if earlier_index >= 0:
                earlier_closing_price = 0
                try:
                    closing_price_string = stock_data[earlier_index][closing_price_index].replace(',', '')
                    earlier_closing_price = float(closing_price_string)
                except ValueError as e:
                    logger.error(f"(TWSE) Illegal closing price in stock: {stock_number}, price string: {closing_price_string}")
                    return StockPriceDifference(None, None, None, None)
            else:
                # Fetch additional records from earlier months
                earlier_records = []
                remaining_records = n_records

                while remaining_records > 0:
                    # Delay 2 seconds to avoid high frequency request blocking
                    time.sleep(2)
                    # Calculate the first day of the previous month
                    first_day_of_month -= timedelta(days=1)
                    formatted_date = first_day_of_month.strftime('%Y%m%d')

                    # Construct the URL for fetching additional data
                    url = f'https://www.twse.com.tw/rwd/en/afterTrading/STOCK_DAY?date={formatted_date}&stockNo={stock_number}&response=json'

                    # Make the request and parse the JSON response
                    additional_data = fetch_data(url)

                    # Check if the request was successful
                    if additional_data.get('stat') == 'OK':
                        # Extract the additional data
                        additional_stock_data = additional_data['data']

                        # Add the additional data to the earlier_records list
                        earlier_records.extend(additional_stock_data)
                        remaining_records -= len(additional_stock_data)
                    else:
                        break

                # Check if there are enough records after fetching additional data
                if earlier_index < 0 and abs(earlier_index) < len(earlier_records):
                    try:
                        closing_price_string = earlier_records[earlier_index][closing_price_index].replace(',', '')
                        earlier_closing_price = float(closing_price_string)
                    except ValueError as e:
                        logger.error(f"(TWSE) Illegal closing price in stock: {stock_number}, price string: {closing_price_string}")
                        return StockPriceDifference(None, None, None, None)
                else:
                    logger.error(f"(TWSE) Not enough records for stock: {stock_number}")
                    return StockPriceDifference(None, None, None, None)

            # Calculate the difference between the latest and earlier Closing Prices
            price_difference = input_date_closing_price - earlier_closing_price

            # Calculate the percentage difference
            percentage_difference = (price_difference / earlier_closing_price) * 100

            # Round the results to a specific number of decimal places
            rounded_price_difference = round(price_difference, 2)
            rounded_percentage_difference = round(percentage_difference, 2)

            return StockPriceDifference(rounded_price_difference, rounded_percentage_difference, input_date_closing_price, earlier_closing_price)
        else:
            logger.error(f"(TWSE) Input date not found in the data, date: {formatted_date} stock: {stock_number}")
            return StockPriceDifference(None, None, None, None)
    else:
        logger.debug(f"(TWSE) Fail to retrieve data for stock: {stock_number}")
        return StockPriceDifference(None, None, None, None)

def get_taiwan_date_string(date_time: datetime):
    year = date_time.year

    # Calculate the Taiwan year
    taiwan_year = year - 1911

    # Create the Taiwan date string with year for aaData searching
    taiwan_date_string_with_year = f'{taiwan_year}/{date_time.strftime("%m/%d")}'
    return taiwan_date_string_with_year

def get_taiwan_date_url_string(date_time: datetime):
    year = date_time.year

    # Calculate the Taiwan year
    taiwan_year = year - 1911

    # Create the Taiwan date string (month and year only) for URL
    taiwan_date_string_for_url = f'{taiwan_year}/{date_time.strftime("%m")}'
    taiwan_date_string_for_url_encoded = quote(taiwan_date_string_for_url)
    return taiwan_date_string_for_url_encoded

def get_tpex_stock_price_difference(stock_number, date_time_string, n_records):
    # Parse input date_time to extract the year
    input_date = datetime.strptime(date_time_string, '%Y%m%d')
    first_day_of_month = input_date.replace(day=1)

    taiwan_date_string_for_url_encoded = get_taiwan_date_url_string(input_date)

    # Construct the URL for fetching data from TPEx
    url = f'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php?l=zh-tw&d={taiwan_date_string_for_url_encoded}&stkno={stock_number}'

    # Make the request and parse the JSON response
    data = fetch_data(url)

    # Define the field mapping structure
    field_mapping = {
        "Date": 0,
        "Trade Volume": 1,
        "Trade Value": 2,
        "Opening Price": 3,
        "Highest Price": 4,
        "Lowest Price": 5,
        "Closing Price": 6,
        "Change": 7,
        "Transaction": 8
    }

    # Check if the request was successful
    if data.get('iTotalRecords', 0) > 0:
        # Extract the data
        stock_data = data['aaData']

         # Create the Taiwan date string with year for aaData searching
        taiwan_date_string_with_year = get_taiwan_date_string(input_date)

        # Find the index of the input date in the data
        input_date_index = next((i for i, record in enumerate(stock_data) if record[field_mapping["Date"]] == taiwan_date_string_with_year), None)

        if input_date_index is not None:
            # Get the Closing Price for the input date
            input_date_closing_price = float(stock_data[input_date_index][field_mapping["Closing Price"]].replace(',', ''))

            # Find the index of the earlier record based on n_records
            earlier_index = input_date_index - n_records

            # Check if there are enough earlier records in the current list
            if earlier_index >= 0:
                earlier_closing_price = 0
                try:
                    closing_price_string = stock_data[earlier_index][field_mapping["Closing Price"]].replace(',', '')
                    earlier_closing_price = float(closing_price_string)
                except ValueError as e:
                    logger.error(f"(TPEX) Illegal closing price in stock: {stock_number}, price string: {closing_price_string}")
                    return StockPriceDifference(None, None, None, None)
            else:
                # Fetch additional records from earlier months
                earlier_records = []
                remaining_records = n_records

                while remaining_records > 0:
                    # Delay 2 seconds to avoid high frequency request blocking
                    time.sleep(2)
                    # Calculate the first day of the previous month
                    first_day_of_month -= timedelta(days=1)
                    taiwan_date_string_for_url_encoded = get_taiwan_date_url_string(first_day_of_month)

                    # Construct the URL for fetching additional data
                    url = f'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php?l=zh-tw&d={taiwan_date_string_for_url_encoded}&stkno={stock_number}'

                    # Make the request and parse the JSON response
                    additional_data = fetch_data(url)

                    # Check if the request was successful
                    if data.get('iTotalRecords', 0) > 0:
                        # Extract the additional data
                        additional_stock_data = additional_data['aaData']

                        # Add the additional data to the earlier_records list
                        earlier_records.extend(additional_stock_data)
                        remaining_records -= len(additional_stock_data)
                    else:
                        break

                # Check if there are enough records after fetching additional data
                if earlier_index < 0 and abs(earlier_index) < len(earlier_records):
                    try:
                        closing_price_string = additional_stock_data[earlier_index][field_mapping["Closing Price"]].replace(',', '')
                        earlier_closing_price = float(closing_price_string)
                    except ValueError as e:
                        logger.error(f"(TPEX) Illegal closing price in stock: {stock_number}, price string: {closing_price_string}")
                        return StockPriceDifference(None, None, None, None)
                else:
                    logger.error(f"(TPEX) Not enough records for stock: {stock_number}")
                    return StockPriceDifference(None, None, None, None)

            # Calculate the difference between the latest and earlier Closing Prices
            price_difference = input_date_closing_price - earlier_closing_price

            # Calculate the percentage difference
            percentage_difference = (price_difference / earlier_closing_price) * 100

            # Round the results to a specific number of decimal places
            rounded_price_difference = round(price_difference, 2)
            rounded_percentage_difference = round(percentage_difference, 2)

            return StockPriceDifference(rounded_price_difference, rounded_percentage_difference, input_date_closing_price, earlier_closing_price)
        else:
            logger.error(f"(TPEX) Input date not found in the data, date: {taiwan_date_string_for_url_encoded} stock: {stock_number}")
            return StockPriceDifference(None, None, None, None)
    else:
        logger.debug(f"(TPEX) Fail to retrieve data for stock: {stock_number}")
        return StockPriceDifference(None, None, None, None)

def get_stock_data(stock_number, date_time, n_records):

    # Attempt to get stock data using TWSE (priority)
    stock_result = get_stock_price_difference(stock_number, date_time, n_records)

    # If TWSE data is not available, try getting data from TPEx
    if stock_result.input_date_closing_price is None:
        tpex_result = get_tpex_stock_price_difference(stock_number, date_time, n_records)
        return tpex_result
    else:
        return stock_result

def get_stock_data_today(stock_number, n_records):
    # Get today's date in the required format
    today_date = datetime.now().strftime('%Y%m%d')

    # Use today's date as the input for the original get_stock_data function
    return get_stock_data(stock_number, today_date, n_records)

# Example usage for TWSE:
twse_stock_number = "1303"
twse_date_time = "20231101"
twse_n_records = 5

twse_result = get_stock_price_difference(twse_stock_number, twse_date_time, twse_n_records)
print("TWSE Results:")
print(f"The price difference is: {twse_result.price_difference}")
print(f"The percentage difference is: {twse_result.percentage_difference}%")
print(f"The closing price on the input date is: {twse_result.input_date_closing_price}")
print(f"The closing price {twse_n_records} days earlier is: {twse_result.earlier_closing_price}")

# Example usage for TPEx:
tpex_stock_number = "1815"
tpex_date_time = "20231205"
tpex_n_records = 10

tpex_result = get_tpex_stock_price_difference(tpex_stock_number, tpex_date_time, tpex_n_records)
print("\nTPEx Results:")
print(f"The price difference is: {tpex_result.price_difference}")
print(f"The percentage difference is: {tpex_result.percentage_difference}%")
print(f"The closing price on the input date is: {tpex_result.input_date_closing_price}")
print(f"The closing price {tpex_n_records} days earlier is: {tpex_result.earlier_closing_price}")

# Example usage for get_stock_data:
stock_number = "1303"
date_time = "20231101"  # Normal date-time format
n_records = 2

result = get_stock_data(stock_number, date_time, n_records)

if result.input_date_closing_price is not None:
    print("\nget_stock_data Results:")
    print(f"The price difference is: {result.price_difference}")
    print(f"The percentage difference is: {result.percentage_difference}%")
    print(f"The closing price on the input date is: {result.input_date_closing_price}")
    print(f"The closing price {n_records} days earlier is: {result.earlier_closing_price}")
else:
    print("No stock data available.")

# Example usage for get_stock_data_today:
stock_number = "1303"
n_records = 2

result_today = get_stock_data_today(stock_number, n_records)

if result_today.input_date_closing_price is not None:
    print("\nget_stock_data_today Results for Today:")
    print(f"The price difference is: {result_today.price_difference}")
    print(f"The percentage difference is: {result_today.percentage_difference}%")
    print(f"The closing price on the input date is: {result_today.input_date_closing_price}")
    print(f"The closing price {n_records} days earlier is: {result_today.earlier_closing_price}")
else:
    print("No stock data available for today.")
