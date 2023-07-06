from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.database.dao.BaseDao import BaseDao
from src.database.database import async_session_maker
from src.database.model.User import User


class UserDao(BaseDao):
    model = User

    @classmethod
    async def find_one_or_none_user(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).options(selectinload(cls.model.referrals)).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def count_filtered(cls, *filters):
        async with async_session_maker() as session:
            query = select(func.count(cls.model.id)).where(*filters)
            result = await session.execute(query)
            return result.scalar()

    @classmethod
    async def top_balance_users(cls, top_limit=10):
        async with async_session_maker() as session:
            query = select(cls.model).order_by(cls.model.balance.desc()).limit(top_limit)
            result = await session.execute(query)
            return result.scalars().all()
