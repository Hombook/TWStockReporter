# Overview

This is the POC(Proof of Concept) version of Taiwan stock daily reporter.

Features:
* Scrap data from Goodinfo.
    * https://goodinfo.tw/tw2/StockList.asp?RPT_TIME=&MARKET_CAT=智慧選股&INDUSTRY_CAT=外資連買+–+日%40%40外資連續買超%40%40外資連續買超+–+日
* Filter out stocks that doesn't match the criteria:
    * 3 or more consecutive days with potisive total buying numbers from foreign investors.
        * The consecutive days is configurable through config file.
* Send the data as CSV to a given Discord channel.
    * By using a webhook.
    * Configurable through config file.
* Script will be run at 16:15, Monday to Friday.

# System Requirements

**OS:** Ubuntu Minimal 22.04 LTS (Jammy Jellyfish)  
**Hardware:** Anything equals or better than Google GCE e2-micro instance:
* 2 CPUs
* 1 GB RAM

# Install

1. Follow this guide to create a Discord webhook: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
2. Replace **YOUR_DISCORD_WEBHOOK_URL** with your webhook URL in config.json
    * Keep the URL inside the quotation mark.
```json
{
    "min_cont_buy_days": 3,
    "discord_webhook_url": "https://discord.com/api/webhooks/XXXX"
}
```
3. Run install script
```bash
$ chmod +x install.sh
$ ./install.sh
```

# Uninstall

```bash
$ chmod +x uninstall.sh
$ ./uninstall.sh
```