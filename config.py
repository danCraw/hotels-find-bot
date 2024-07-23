import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

YANDEX_SEARCH_ORGANIZATION_URL = os.getenv('YANDEX_SEARCH_ORGANIZATION_URL')
OPEN_ROUTE_SERVICE_API_URL = os.getenv('OPEN_ROUTE_SERVICE_API_URL')
YANDEX_GEOCODE_API_URL = os.getenv('YANDEX_GEOCODE_API_URL')

YANDEX_GEOCODE_API_KEY = os.getenv('YANDEX_GEOCODE_API_KEY')
YANDEX_SEARCH_ORGANIZATION_API = os.getenv('YANDEX_SEARCH_ORGANIZATION_API')
OPEN_ROUTE_SERVICE_API_KEY = os.getenv('OPEN_ROUTE_SERVICE_API_KEY')
YANDEX_SEARCH_API_KEY = os.getenv('YANDEX_SEARCH_API_KEY')

# REVERSE_GEOCODE_URL = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_API}&geocode={lon},{lat}&format=json'
# CITY_GEOCODE_URL = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_API}&geocode={city}&format=json'

