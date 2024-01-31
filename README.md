# Overview
WIP...

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