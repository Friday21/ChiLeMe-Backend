import datetime
import logging
import yfinance as yf
from django.core.management.base import BaseCommand
from wxcloudrun.models import Asset, StockPrice

logger = logging.getLogger('log')

class Command(BaseCommand):
    help = 'Update stock prices from yfinance'

    def handle(self, *args, **options):
        logger.info('Starting stock price update...')
        
        # 1. Get unique stock codes
        stock_codes = Asset.objects.filter(type='stock').values_list('stock_code', flat=True).distinct()
        stock_codes = [code for code in stock_codes if code] # Filter out empty/None
        
        if not stock_codes:
            logger.info('No stock codes found.')
            return

        # 2. Fetch Exchange Rates
        try:
            usd_cny = yf.Ticker("CNY=X").history(period="1d")['Close'].iloc[-1]
            hkd_cny = yf.Ticker("HKDCNY=X").history(period="1d")['Close'].iloc[-1]
            logger.info(f"Exchange Rates - USD/CNY: {usd_cny}, HKD/CNY: {hkd_cny}")
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            # Fallback or exit? Let's set defaults or exit. 
            # Better to exit or use approximate if critical, but for now let's log and maybe fail for those needing conversion.
            usd_cny = 7.2
            hkd_cny = 0.92

        today = datetime.date.today()

        for code in stock_codes:
            logger.info(f"Processing stock code: {code}")
            
            ticker = None
            price = None
            currency = 'CNY'
            
            # Try different suffixes
            # Priority: US (no suffix) -> HK (.HK) -> A-Share (.SS, .SZ)
            suffixes = ['', '.HK', '.SS', '.SZ']
            
            for suffix in suffixes:
                try:
                    symbol = f"{code}{suffix}"
                    # Optimization: Check if it looks like a code for a specific market to avoid unnecessary requests
                    # E.g. 0700 is likely HK, 600xxx is likely SS. But user asked to try in order.
                    
                    t = yf.Ticker(symbol)
                    # fast_info is faster than info
                    # history(period='1d') is reliable
                    hist = t.history(period="1d")
                    
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        # Get currency
                        # info might be slow, but needed for currency. 
                        # Alternatively, guess based on suffix.
                        if suffix == '':
                            currency = 'USD' # Assumption for US
                            # Double check if it's actually found and valid
                            # Sometimes yfinance returns data for invalid symbols? No, usually empty history.
                        elif suffix == '.HK':
                            currency = 'HKD'
                        elif suffix in ['.SS', '.SZ']:
                            currency = 'CNY'
                            
                        # Try to get actual currency from metadata if possible, but history doesn't have it.
                        # t.fast_info['currency'] is available in newer yfinance
                        try:
                            if hasattr(t, 'fast_info') and t.fast_info.currency:
                                currency = t.fast_info.currency
                        except:
                            pass
                            
                        logger.info(f"Found {symbol}: Price {price} {currency}")
                        break
                except Exception as e:
                    logger.warning(f"Error fetching {code}{suffix}: {e}")
                    continue
            
            if price is not None:
                # Convert to CNY
                price_cny = price
                if currency == 'USD':
                    price_cny = price * usd_cny
                elif currency == 'HKD':
                    price_cny = price * hkd_cny
                
                # Save to DB
                StockPrice.objects.update_or_create(
                    stock_code=code,
                    date=today,
                    defaults={'price': price_cny}
                )
                logger.info(f"Saved {code}: {price_cny} CNY")
            else:
                logger.warning(f"Could not find price for {code}")

        logger.info('Stock price update completed.')
