import asyncio

from src.bot.parsing.sites.depop import run_depop
from src.bot.parsing.sites.grailed import run_grailed
from src.bot.parsing.sites.poshmark import run_poshmark
from src.bot.parsing.sites.schpock import run_schpock
from src.bot.parsing.sites.vinted import run_vinted
from src.bot.parsing.sites.wallapop import run_wallapop
from src.database.dao.Associations import UserFilterSubscriptionDao
from src.database.dao.FilterDao import FilterDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.utils.constants import parsing_tasks


async def run_parsing(user_id, subscription_id, filter_id):
    subscription = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    splitted = filter_entity.value.split("\n")[:-1]
    if "DEPOP" in subscription:
        await handle_depop(subscription, splitted, user_id)
    elif "GRAILED" in subscription:
        await handle_grailed(subscription, splitted, user_id)
    elif "POSHMARK" in subscription:
        await handle_poshmark(subscription, splitted, user_id)
    elif "SCHPOCK" in subscription:
        await handle_schpock(subscription, splitted, user_id)
    elif "VINTED" in subscription:
        await handle_vinted(subscription, splitted, user_id)
    elif "WALLAPOP" in subscription:
        await handle_wallapop(subscription, splitted, user_id)

    user_filter_subscriptions = await UserFilterSubscriptionDao.find_all(user_id=user_id, is_favourite=False)
    ids_to_delete = [filter_entity.filter_id for filter_entity in
                     user_filter_subscriptions]
    await FilterDao.delete_by_ids(ids_to_delete)


async def handle_depop(subscription, splitted, user_id):
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'].lower() != "не использовать фильтр" else ["", ""]

    quantity_of_ads = dict_arguments['Кол-во проданных товаров продавца'] if dict_arguments[
                                                                                 'Кол-во проданных товаров продавца'].lower() != "не использовать фильтр" else ""

    seller_rating = dict_arguments['Рейтинг продавца'] if dict_arguments[
                                                              'Рейтинг продавца'].lower() != "не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'].lower() != "не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()
    if country == "uk":
        country = "gb"
    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(run_depop(urls, prices[0], prices[1],
                                                               quantity_of_ads, seller_rating,
                                                               ad_created_date, country,
                                                               user_id))


async def handle_grailed(subscription, splitted, user_id):
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'].lower() != "не использовать фильтр" else ["", ""]

    items_quantity = dict_arguments['Кол-во обьявлений продавца'] if dict_arguments[
                                                                         'Кол-во обьявлений продавца'].lower() != "не использовать фильтр" else ""

    items_quantity_sold = dict_arguments['Кол-во проданных товаров продавца'] if dict_arguments[
                                                                                     'Кол-во проданных товаров продавца'].lower() != "не использовать фильтр" else ""

    seller_registration_date = dict_arguments['Дата регистрации продавца'] if dict_arguments[
                                                                                  'Дата регистрации продавца'].lower() != "не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'].lower() != "не использовать фильтр" else ""

    seller_rating = dict_arguments['Рейтинг продавца'] if dict_arguments[
                                                              'Рейтинг продавца'].lower() != "не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()
    if country == "uk":
        country = "United Kingdom"
    elif country == "us":
        country = "United States"
    elif country == "au":
        country = "Australia/NZ"
    elif country == "ca":
        country = "Canada"
    elif country == "asia":
        country = "Asia"
    elif country == "eu":
        country = "Europe"

    price_min = int(prices[0]) if prices[0] != "" else 0
    price_max = int(prices[1]) if prices[1] != "" else 200000

    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(
            run_grailed(urls, country, items_quantity, items_quantity_sold, seller_registration_date,
                        ad_created_date, seller_rating, user_id, price_min, price_max))


async def handle_poshmark(subscription, splitted, user_id):
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'].lower() != "не использовать фильтр" else ["", ""]

    items_quantity = dict_arguments['Кол-во обьявлений продавца'] if dict_arguments[
                                                                         'Кол-во обьявлений продавца'].lower() != "не использовать фильтр" else ""

    seller_registration_date = dict_arguments['Дата регистрации продавца'] if dict_arguments[
                                                                                  'Дата регистрации продавца'].lower() != "не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'].lower() != "не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()

    price_min = int(prices[0]) if prices[0] != "" else 0
    price_max = int(prices[1]) if prices[1] != "" else 200000

    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(
            run_poshmark(urls, country, items_quantity, seller_registration_date,
                         ad_created_date, user_id, price_min, price_max))


async def handle_schpock(subscription, splitted, user_id):
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'].lower() != "не использовать фильтр" else ["", ""]

    items_quantity = dict_arguments['Кол-во обьявлений продавца'] if dict_arguments[
                                                                         'Кол-во обьявлений продавца'].lower() != "не использовать фильтр" else ""

    items_quantity_sold = dict_arguments['Кол-во проданных товаров продавца'] if dict_arguments[
                                                                                     'Кол-во проданных товаров продавца'].lower() != "не использовать фильтр" else ""

    seller_registration_date = dict_arguments['Дата регистрации продавца'] if dict_arguments[
                                                                                  'Дата регистрации продавца'].lower() != "не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'].lower() != "не использовать фильтр" else ""

    seller_rating = dict_arguments['Рейтинг продавца'] if dict_arguments[
                                                              'Рейтинг продавца'].lower() != "не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()

    price_min = int(prices[0]) if prices[0] != "" else 0
    price_max = int(prices[1]) if prices[1] != "" else 200000

    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(
            run_schpock(urls, country, items_quantity, items_quantity_sold, seller_registration_date,
                        ad_created_date, seller_rating, user_id, price_min, price_max))


async def handle_vinted(subscription, splitted, user_id):
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'].lower() != "не использовать фильтр" else ["", ""]

    items_quantity = dict_arguments['Кол-во обьявлений продавца'] if dict_arguments[
                                                                         'Кол-во обьявлений продавца'].lower() != "не использовать фильтр" else ""

    items_quantity_sold = dict_arguments['Кол-во проданных товаров продавца'] if dict_arguments[
                                                                                     'Кол-во проданных товаров продавца'].lower() != "не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'].lower() != "не использовать фильтр" else ""

    seller_rating = dict_arguments['Рейтинг продавца'] if dict_arguments[
                                                              'Рейтинг продавца'].lower() != "не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()

    price_min = int(prices[0]) if prices[0] != "" else 0
    price_max = int(prices[1]) if prices[1] != "" else 200000

    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(
            run_vinted(urls, country, items_quantity, items_quantity_sold,
                       ad_created_date, seller_rating, user_id, price_min, price_max))


async def handle_wallapop(subscription, splitted, user_id):
    dict_arguments = {}
    for i in splitted:
        key, value = i.split(" : ")
        dict_arguments[key] = value
    urls_list = dict_arguments["Ссылки"].split(",")
    urls = [url for url in urls_list if url != '']
    prices = dict_arguments['Цена'].split("-") if dict_arguments[
                                                      'Цена'].lower() != "не использовать фильтр" else ["", ""]

    items_quantity = dict_arguments['Кол-во обьявлений продавца'] if dict_arguments[
                                                                         'Кол-во обьявлений продавца'].lower() != "не использовать фильтр" else ""

    items_quantity_sold = dict_arguments['Кол-во проданных товаров продавца'] if dict_arguments[
                                                                                     'Кол-во проданных товаров продавца'].lower() != "не использовать фильтр" else ""

    seller_registration_date = dict_arguments['Дата регистрации продавца'] if dict_arguments[
                                                                                  'Дата регистрации продавца'].lower() != "не использовать фильтр" else ""

    ad_created_date = dict_arguments['Дата создания объявления'] if dict_arguments[
                                                                        'Дата создания объявления'].lower() != "не использовать фильтр" else ""

    seller_rating = dict_arguments['Рейтинг продавца'] if dict_arguments[
                                                              'Рейтинг продавца'].lower() != "не использовать фильтр" else ""

    country = subscription.split(".")[1].lower()

    price_min = int(prices[0]) if prices[0] != "" else 0
    price_max = int(prices[1]) if prices[1] != "" else 200000

    if user_id not in parsing_tasks or parsing_tasks[user_id].done():
        parsing_tasks[user_id] = asyncio.create_task(
            run_wallapop(urls, country, items_quantity, items_quantity_sold, seller_registration_date,
                         ad_created_date, seller_rating, user_id, price_min, price_max))
