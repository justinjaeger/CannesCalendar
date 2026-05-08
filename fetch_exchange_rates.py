from datetime import datetime, timedelta
import requests
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fetch_exchange_rates():
    for i in range(0, 6):
        date = (datetime.now() - timedelta(days=i*30)).replace(day=1).strftime('%Y-%m-%d')
        # if ExchangeRate.objects.filter(date=date).exists():
        #     logger.info(f"[EXCHANGE_RATE] Rates already exist for {date}, skipping")
        #     continue
        try:
            response = requests.get(f'https://api.fxratesapi.com/historical?date={date}&places=5&api_key=fxr_live_ffcd8f78a93bbf629bc95f06546cd226f085')
            rates = response.json()['rates']
            print(f"[DEBUG] About to log rates for {date}, count: {len(rates)}")
            logger.info(f"[EXCHANGE_RATE] Got {len(rates)} rates from API for {date}")
            for currency in rates:
                pass  # No operation, placeholder for future code
            logger.info(f"[EXCHANGE_RATE] Successfully stored all rates for {date}")
        except Exception as e:
            logger.error(f"[EXCHANGE_RATE_ERROR] Failed to fetch exchange rates for {date}: {e}")
            continue
    logger.info("[EXCHANGE_RATE] Task completed successfully")
    return None 

fetch_exchange_rates()