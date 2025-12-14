#!/bin/bash

# Start cron
service cron start

# Run the update command once on startup (optional, but good for testing)
# python3 manage.py update_stock_prices &

# Start Gunicorn
/root/.local/bin/gunicorn --bind 0.0.0.0:80 --workers 4 wxcloudrun.wsgi:application
