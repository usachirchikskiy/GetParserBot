import aiohttp

from src.config import COIN_MARKET_API_KEY, SANDBOX_COIN_MARKET_API, COIN_MARKET_API


class CoinMarket:
    __api_key: str
    _instance = None

    @staticmethod
    def get_instance():
        if CoinMarket._instance is None:
            CoinMarket._instance = CoinMarket(COIN_MARKET_API_KEY)
        return CoinMarket._instance

    def __init__(self, api_key):
        if CoinMarket._instance is not None:
            raise Exception("CoinMarket class can only have one instance.")
        CoinMarket.__api_key = api_key

    @staticmethod
    async def get_in_crypto(asset: str, amount: float):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    "https://{}/v2/tools/price-conversion".format(SANDBOX_COIN_MARKET_API),  # TODO change
                    params={"amount": amount, "symbol": "RUB", "convert": asset},
                    headers={"X-CMC_PRO_API_KEY": CoinMarket.__api_key},
            ) as response:
                return (await response.json())["data"]['RUB']["quote"][asset]["price"]  # TODO change
