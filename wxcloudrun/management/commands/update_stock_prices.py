import datetime
import logging
import decimal
import time
import akshare as ak
import pandas as pd
from django.core.management.base import BaseCommand
from wxcloudrun.models import Asset, StockPrice

logger = logging.getLogger('log')

class Command(BaseCommand):
    help = 'Update stock prices from yfinance'

    def handle(self, *args, **options):
        logger.info('Starting stock price update (akshare)...')
        
        # 1. Get unique stock codes
        stock_codes = Asset.objects.filter(type='stock').values_list('stock_code', flat=True).distinct()
        stock_codes = [code for code in stock_codes if code] # Filter out empty/None
        
        if not stock_codes:
            logger.info('No stock codes found.')
            return

        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=5)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")

        # 2. Fetch Exchange Rates
        usd_cny = 7.2
        hkd_cny = 0.92
        try:
            # currency_boc_sina: symbol="美元"
            # Returns DataFrame with columns like "日期", "中行汇买价", ...
            # We use "中行折算价" (Conversion Rate) which is usually per 100 units
            usd_df = ak.currency_boc_sina(symbol="美元", start_date=start_date, end_date=end_date)
            if not usd_df.empty and '中行折算价' in usd_df.columns:
                usd_cny = float(usd_df['中行折算价'].iloc[-1]) / 100
            
            hkd_df = ak.currency_boc_sina(symbol="港币", start_date=start_date, end_date=end_date)
            if not hkd_df.empty and '中行折算价' in hkd_df.columns:
                hkd_cny = float(hkd_df['中行折算价'].iloc[-1]) / 100
                
            logger.info(f"Exchange Rates - USD/CNY: {usd_cny}, HKD/CNY: {hkd_cny}")
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")

        for code in stock_codes:
            logger.info(f"Processing stock code: {code}")
            
            price = None
            currency = 'CNY'
            
            # Strategy: Try A-share -> HK -> US
            
            # 1. Try A-Share (6 digits)
            if code.isdigit() and len(code) == 6:
                try:
                    df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                    if not df.empty:
                        price = df['收盘'].iloc[-1]
                        currency = 'CNY'
                        logger.info(f"Found A-Share {code}: {price}")
                except Exception as e:
                    logger.warning(f"A-Share check failed for {code}: {e}")
            
            # 2. Try HK Share (5 digits)
            if not price and code.isdigit() and len(code) == 5:
                try:
                    df = ak.stock_hk_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                    if not df.empty:
                        price = df['收盘'].iloc[-1]
                        currency = 'HKD'
                        logger.info(f"Found HK-Share {code}: {price}")
                except Exception as e:
                    logger.warning(f"HK-Share check failed for {code}: {e}")

            # 3. Try US Share (Letters or other formats)
            if not price:
                # Try prefixes for EastMoney: 105 (Nasdaq), 106 (NYSE), 107 (Amex)
                prefixes = ["105.", "106.", "107."]
                for prefix in prefixes:
                    try:
                        symbol = f"{prefix}{code}"
                        df = ak.stock_us_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                        if not df.empty:
                            price = df['收盘'].iloc[-1]
                            currency = 'USD'
                            logger.info(f"Found US-Share {symbol}: {price}")
                            break
                    except:
                        continue
            
            if price is not None:
                # Convert to CNY
                price_cny = float(price)
                if currency == 'USD':
                    price_cny = price_cny * usd_cny
                elif currency == 'HKD':
                    price_cny = price_cny * hkd_cny
                
                # Save to DB
                StockPrice.objects.update_or_create(
                    stock_code=code,
                    date=today,
                    defaults={'price': price_cny}
                )
                logger.info(f"Saved {code}: {price_cny} CNY")

                # Update Assets
                assets = Asset.objects.filter(stock_code=code, type='stock')
                for asset in assets:
                    if asset.shares:
                        # Ensure price_cny is Decimal for calculation
                        asset.value = asset.shares * decimal.Decimal(str(price_cny))
                        asset.save()
                        logger.info(f"Updated Asset {asset.id} value to {asset.value}")
            else:
                logger.warning(f"Could not find price for {code}")

        logger.info('Stock price update completed.')
