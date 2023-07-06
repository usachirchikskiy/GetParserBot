# async def test():
#     async with async_session_maker() as session:
#         user1_id = (await UserDao.add(**{'balance': 1})).id
#         user2_id = (await UserDao.add(**{'balance': 2})).id
#
#         # subscription_insert = insert(Subscription).values([
#         #     {'name': 'Subscription1', 'price_one_day': 250},
#         #     {'name': 'Subscription2', 'price_one_day': 350}
#         # ])
#         #
#         subscription1_id = (await SubscriptionDao.add(**{'name': 'Subscription1', 'price_one_day': 250})).id
#         subscription2_id = (await SubscriptionDao.add(**{'name': 'Subscription2', 'price_one_day': 350})).id
#
#         filter1_id = (await FilterDao.add(**{'value': "1"})).id
#         filter2_id = (await FilterDao.add(**{'value': "2"})).id
#
#         filter_association_insert = insert(UserSubscriptionFilterAssociation).values([
#             {"user_id": user1_id, "subscription_id": subscription1_id, "filter_id": filter1_id},
#             {"user_id": user2_id, "subscription_id": subscription2_id, "filter_id": filter2_id},
#             # {"user_id": user1_id, "subscription_id": subscription2_id, "filter_id": filter1_id},
#             # {"user_id": user2_id, "subscription_id": subscription2_id, "filter_id": filter2_id},
#         ])
#         await session.execute(filter_association_insert)
#         await session.commit()
#
#         delete_stmt = delete(User).where(User.id == user1_id)
#         delete_stmt1 = delete(Filter).where(Filter.id == filter2_id)
#         await session.execute(delete_stmt)
#         await session.execute(delete_stmt1)
#         await session.commit()
from src.utils.utils import convert_from_moscow_to_utc

convert_from_moscow_to_utc()