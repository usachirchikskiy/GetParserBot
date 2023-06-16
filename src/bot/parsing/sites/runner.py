import asyncio

from src.bot.parsing.sites.depop import run_depop
from src.database.dao.Associations import UserFilterSubscriptionDao
from src.database.dao.FilterDao import FilterDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.utils.constants import parsing_tasks
from src.utils.utils import get_currency


async def run_parsing(user_id, subscription_id, filter_id):
    subscription = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name
    await handle_depop(subscription, filter_id, user_id)

    user_filter_subscriptions = await UserFilterSubscriptionDao.find_all(user_id=user_id, is_favourite=False)
    ids_to_delete = [filter_entity.filter_id for filter_entity in
                     user_filter_subscriptions]
    await FilterDao.delete_by_ids(ids_to_delete)


async def handle_depop(subscription, filter_id, user_id):

    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    splitted = filter_entity.value.split("\n")[:-1]
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'] != "Не использовать фильтр" else ["", ""]

    quantity_of_ads = dict_arguments['Кол-во проданных товаров продавца'] if dict_arguments[
                                                                                 'Кол-во проданных товаров продавца'] != "Не использовать фильтр" else ""

    seller_rating = dict_arguments['Рейтинг продавца'] if dict_arguments[
                                                              'Рейтинг продавца'] != "Не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'] != "Не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()
    if country == "uk":
        country = "gb"
    currency = get_currency(country)
    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(run_depop(urls, prices[0], prices[1],
                                                               quantity_of_ads, seller_rating,
                                                               # seller_registration_date,
                                                               ad_created_date, country,
                                                               currency, user_id))


async def handle_grailed():
    pass

async def handle_schpock():
    pass