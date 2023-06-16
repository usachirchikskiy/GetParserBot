import copy
from datetime import datetime, timedelta

from sqlalchemy import select

from src.database.dao.BaseDao import BaseDao
from src.database.database import async_session_maker
from src.database.model.User import UserSubscriptionAssociation, UserSubscriptionFilterAssociation, \
    UserPaymentSystemAssociation


# from src.database.model.User import subscription_association_table, filter_association_table, payment_association_table


class UserSubscriptionDao(BaseDao):
    model = UserSubscriptionAssociation

    @classmethod
    async def is_active(cls, **data):
        subscription = await cls.find_one_or_none(**data)
        if not subscription:
            return False
        current_time = datetime.now()
        if subscription.expired_at is None:
            return False
        if current_time > subscription.expired_at:
            return False
        return True

    @classmethod
    async def add_or_update(cls, days, **data):
        exist = await cls.find_one_or_none(**data)
        expired_at = datetime.now() + timedelta(days=days)
        data['expired_at'] = expired_at
        if not exist:
            await cls.add(**data)
        else:
            await cls.update(exist.id, **data)


class UserFilterSubscriptionDao(BaseDao):
    model = UserSubscriptionFilterAssociation

    @classmethod
    async def get_last_added(cls, user_id):
        query = select(UserSubscriptionFilterAssociation). \
            filter_by(user_id=user_id). \
            order_by(UserSubscriptionFilterAssociation.created_at.desc()). \
            limit(1)
        async with async_session_maker() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()


class UserPaymentSystemDao(BaseDao):
    model = UserPaymentSystemAssociation

    @classmethod
    async def add_or_update(cls, **data):
        insert_update_data = copy.deepcopy(data)
        data.pop('type')
        data.pop('payment_system_id')
        exist = await cls.find_one_or_none(**data)
        if not exist:
            await cls.add(**insert_update_data)
        else:
            await cls.update(exist.id, **insert_update_data)
