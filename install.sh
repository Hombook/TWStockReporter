#!/bin/bash

# Install Python 3 and pip
sudo apt update
sudo apt-get install cron -y
sudo apt install -y python3 python3-pip

# Install required Python packages
pip3 install requests discord-webhook pandas beautifulsoup4

# Get the path to the current script
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create cron jobs to send daily report at 16:15 pm on weekdays
(crontab -l 2>/dev/null; echo "15 16 * * 1-5 /usr/bin/python3 $SCRIPT_PATH/daily_stock_report.py") | crontab -

echo "Installation complete. Daily stock report script scheduled to run at 16:15 pm on weekdays."
