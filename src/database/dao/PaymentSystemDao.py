from src.database.dao.BaseDao import BaseDao
from src.database.model.User import PaymentSystem


class PaymentSystemDao(BaseDao):
    model = PaymentSystem

    @classmethod
    async def add_payment_systems(self):
        payments = [{"title": "Bitpapa"}, {"title": "Cryptobot"}, {"title": "Payok"}, {"title": None}]
        for payment in payments:
            await self.add_if_not_exists(**payment)
