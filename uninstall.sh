#!/bin/bash

# Get the path to the current script
SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Remove daily report cron jobs
(crontab -l | grep -v "$SCRIPT_PATH/daily_stock_report.py") | crontab -

echo "Uninstallation complete. Daily stock report script unscheduled."
