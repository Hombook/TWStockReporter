#!/bin/bash

# Function to remove an existing schedule
remove_existing_schedule() {
    local script_name=$1
    local existing_schedule=$(crontab -l 2>/dev/null)

    if [[ $existing_schedule == *"$script_name"* ]]; then
        # Remove existing schedule
        (crontab -l | grep -v "$script_name") | crontab -
        echo "Existing schedule for $script_name removed."
    fi
}

# Install Python 3 and pip
sudo apt update
sudo apt-get install cron -y
sudo apt install -y python3 python3-pip

# Install required Python packages
pip3 install requests discord-webhook pandas beautifulsoup4

# Get the path to the current script
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Remove existing schedule for daily_3insti_report.py
remove_existing_schedule "daily_3insti_report.py"

# Remove existing schedule for daily_stock_report.py
remove_existing_schedule "daily_stock_report.py"

# Create cron jobs to send daily report on weekdays
(crontab -l 2>/dev/null; echo "15 16 * * 1-5 /usr/bin/python3 $SCRIPT_PATH/daily_3insti_report.py") | crontab -
(crontab -l 2>/dev/null; echo "0 17 * * 1-5 /usr/bin/python3 $SCRIPT_PATH/daily_stock_report.py") | crontab -


echo "Installation complete. Daily stock report script scheduled to run on weekdays."
crontab -l
