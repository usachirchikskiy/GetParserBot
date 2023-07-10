import copy
from datetime import datetime, timedelta

from sqlalchemy import select, insert, update, exists

from src.database.dao.BaseDao import BaseDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.database.database import async_session_maker
from src.database.model.User import UserSubscriptionAssociation, UserSubscriptionFilterAssociation, \
    UserPaymentSystemAssociation


class UserSubscriptionDao(BaseDao):
    model = UserSubscriptionAssociation

    @classmethod
    async def exists(cls, user_id):
        async with async_session_maker() as session:
            query = select(exists().where(cls.model.user_id == user_id))
            record_exists = await session.execute(query)
            return record_exists.scalar()

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

    @classmethod
    async def add_or_update_all(cls, days, user_id):
        subscriptions = await SubscriptionDao.find_all()

        to_add = []
        to_update = []

        for subscription in subscriptions:
            expired_at = datetime.now() + timedelta(days=days)
            exist = await cls.find_one_or_none(user_id=user_id, subscription_id=subscription.id)
            if not exist:
                to_add.append({"expired_at": expired_at, "user_id": user_id, "subscription_id": subscription.id})
            else:
                to_update.append(
                    {"id": exist.id, "expired_at": expired_at, "user_id": user_id, "subscription_id": subscription.id})

        async with async_session_maker() as session:
            if to_add:
                await session.execute(insert(cls.model).values(to_add))
            if to_update:
                for record in to_update:
                    await session.execute(update(cls.model).where(cls.model.id == record["id"]).values(record))
            await session.commit()


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
