import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
COIN_MARKET_API_KEY = os.environ.get("COIN_MARKET_API_KEY")
SANDBOX_COIN_MARKET_API = os.environ.get("SANDBOX_COIN_MARKET_API")
COIN_MARKET_API = os.environ.get("COIN_MARKET_API")
STATIC = os.environ.get("STATIC")
