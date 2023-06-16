from src.database.dao.BaseDao import BaseDao
from src.database.model.User import Subscription


class SubscriptionDao(BaseDao):
    model = Subscription

    @classmethod
    async def add_subscriptions(self):
        subscriptions = [
            {'name': 'DEPOP.AU', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'DEPOP.DE', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'DEPOP.FR', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'DEPOP.IT', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'DEPOP.UK', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'DEPOP.US', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},

            {'name': 'GRAILED.US', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'GRAILED.UK', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'GRAILED.EU', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'GRAILED.CA', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'GRAILED.AUNZ', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},
            {'name': 'GRAILED.ASIA', 'price_one_day': 250, 'price_three_day': 500, 'price_week': 1000, 'price_month': 4500},

        ]
        for subscription in subscriptions:
            await self.add_if_not_exists(**subscription)


