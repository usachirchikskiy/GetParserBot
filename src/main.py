import logging
from telethon import TelegramClient
from src.api.coin_market.CoinMarket import CoinMarket
from src.api.crypto_pay.CryptoPay import CryptoPay

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

client_bot = TelegramClient("bot", 16819926, "65788ccadd6ccbd8695f19710b41a2fd").start(
    bot_token="6059203083:AAEV8bjjzu32G0ZcKd8ggAo_lqN6-HqwiRc")

client_user_bitpapa = TelegramClient("user_bitpapa", api_id=16819926,
                                     api_hash="65788ccadd6ccbd8695f19710b41a2fd").start()

crypto_pay = CryptoPay.get_instance()
coin_market = CoinMarket.get_instance()




