import logging

from telethon import TelegramClient

from src.api.coin_market.CoinMarket import CoinMarket
from src.api.crypto_pay.CryptoPay import CryptoPay
from src.utils.constants import bot_token, api_hash, user_bitpapa, api_id

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

client_bot = TelegramClient("bot", api_id=api_id, api_hash=api_hash).start(
    bot_token=bot_token)

client_user_bitpapa = TelegramClient(user_bitpapa, api_id=api_id,
                                     api_hash=api_hash).start()

crypto_pay = CryptoPay.get_instance()
coin_market = CoinMarket.get_instance()
