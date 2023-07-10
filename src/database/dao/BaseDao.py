import logging

from sqlalchemy import select, insert, delete, update, exists
from sqlalchemy.exc import SQLAlchemyError

from src.database.database import async_session_maker


class BaseDao:
    model = None

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def find_by_ids(cls, *ids):
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.id.in_(ids))
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def add(cls, **data):
        try:
            query = insert(cls.model).values(**data).returning(cls.model)
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.scalar_one()
        except Exception as e:
            logging.error(f'ERROR {e}')
            return None

    @classmethod
    async def update(cls, id, **data):
        try:
            query = update(cls.model).where(cls.model.id == id).values(**data).returning(cls.model)
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.scalar_one()
        except Exception as e:
            logging.error(f'ERROR {e}')
            return None

    @classmethod
    async def delete(cls, **filter_by):
        async with async_session_maker() as session:
            query = delete(cls.model).filter_by(**filter_by)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def delete_by_ids(cls, ids_to_delete):
        async with async_session_maker() as session:
            query = delete(cls.model).where(cls.model.id.in_(ids_to_delete))
            await session.execute(query)
            await session.commit()

    # Usman`s addings
    @classmethod
    async def add_if_not_exists(cls, **data):
        exist = await cls.find_one_or_none(**data)
        if not exist:
            await cls.add(**data)
