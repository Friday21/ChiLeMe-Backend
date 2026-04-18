#!/bin/bash

# Generate run_update_stock.sh with current environment variables
echo "#!/bin/bash" > /app/run_update_stock.sh
printenv | grep -v "no_proxy" | sed 's/^\(.*\)$/export \1/g' >> /app/run_update_stock.sh
echo "cd /app" >> /app/run_update_stock.sh
echo "/usr/local/bin/python manage.py update_stock_prices >> /var/log/stock_update.log 2>&1" >> /app/run_update_stock.sh
echo "/usr/local/bin/python manage.py process_fixed_items >> /var/log/fixed_items.log 2>&1" >> /app/run_update_stock.sh
chmod +x /app/run_update_stock.sh

# Start cron
service cron start

# Run the update command once on startup (optional, but good for testing)
# python3 manage.py update_stock_prices &

# Start Gunicorn
/root/.local/bin/gunicorn --bind 0.0.0.0:80 --workers 4 wxcloudrun.wsgi:application
