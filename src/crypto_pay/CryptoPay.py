from aiocryptopay import AioCryptoPay, Networks


class CryptoPay:
    __crypto = None
    _instance = None

    def __init__(self):
        if CryptoPay._instance is not None:
            raise Exception("CryptoPay class can only have one instance.")
        CryptoPay._instance = self
        CryptoPay.__crypto = AioCryptoPay(token='7157:AAaWZEjCVrlcYIcBZu3rv43HJ55Ca85YOOE', network=Networks.TEST_NET)

    @staticmethod
    def get_instance():
        if CryptoPay._instance is None:
            CryptoPay._instance = CryptoPay()
        return CryptoPay._instance

    # @staticmethod
    # async def get_me():
    #     return await CryptoPay._instance.__crypto.get_me()
    #
    # @staticmethod
    # async def get_currencies():
    #     return await CryptoPay.__crypto.get_currencies()
    #
    # @staticmethod
    # async def get_balance():
    #     return await CryptoPay.__crypto.get_balance()

    # @staticmethod
    # async def get_exchange_rates():
    #     return await CryptoPay.__crypto.get_exchange_rates()

    @staticmethod
    async def create_invoice(asset, amount):
        return await CryptoPay.__crypto.create_invoice(asset=asset, amount=amount)

    @staticmethod
    async def get_invoice(id):
        return await CryptoPay.__crypto.get_invoices(invoice_ids=id)
