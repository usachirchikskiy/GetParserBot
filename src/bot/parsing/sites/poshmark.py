import asyncio
import json
import logging
import urllib

import aiohttp
import requests
from telethon import Button
from telethon.errors import UserIsBlockedError

from src.main import client_bot
from src.utils.utils import truncate_string, moscow_time


class Poshmark:
    def __init__(self, urls, country, quantity_of_ads, seller_registration_date,
                 ad_created_date, chat_id, price_min, price_max):
        self.price_min = price_min
        self.price_max = price_max
        self.quantity_of_ads = int(quantity_of_ads) if quantity_of_ads != "" else None
        self.ad_created_date = ad_created_date if ad_created_date != "" else None
        self.seller_registration_date = seller_registration_date if seller_registration_date != "" else None
        self.url_ending = self.get_url_ending(country)
        self.currency = self.get_currency(country)
        self.chat_id = chat_id
        self.urls = urls

    def get_query_param(self, query, page):
        return f'{{"filters":{{"department":"All","price_amount_range":[{{"min":{{"val":"{self.price_min}","currency_code":"{self.currency}"}},"max":{{"val":"{self.price_max}","currency_code":"{self.currency}"}}}}],"inventory_status":["available"]}},"query_and_facet_filters":{{"department":"All"}},"query":"{query}","facets":["brand","color","department"],"experience":"all","sizeSystem":"us","max_id":"{page}","count":"100"}}'

    def get_url_ending(self, country):
        if country == "au":
            return "com.au"
        elif country == "us":
            return "com"
        return country

    def get_currency(self, country):
        if country == "au":
            return "AUD"
        elif country == "ca":
            return "CAD"
        elif country == "us":
            return "USD"

    async def fetch_query(self, session, url):
        async with session.get(url, ssl=False) as response:
            return await response.json()

    async def parse_object(self, session, query):
        try:
            page = 1
            query_param = self.get_query_param(query, page)
            url = f"https://poshmark.{self.url_ending}/vm-rest/posts?request={query_param}"
            response = await self.fetch_query(session, url)
            items_length = len(response['data'])
            await self.parse_items(session, response['data'])
            all_items_length = response['more']['total']
            while items_length < all_items_length:
                page += 1
                query_param = self.get_query_param(query, page)
                url = f"https://poshmark.{self.url_ending}/vm-rest/posts?request={query_param}"
                response = await self.fetch_query(session, url)
                items_length += len(response['data'])
                await self.parse_items(session, response['data'])
            await asyncio.sleep(0)
        except asyncio.CancelledError:
            logging.error(f'parse_object Cancelled ERROR')
            raise
        except UserIsBlockedError:
            logging.error(f"parse_object Bot was blocked by the user: {self.chat_id}")
            return
        except Exception as e:
            logging.error(f'parse_object ERROR {e}')

    async def parse_items(self, session, items):
        for item in items:
            seller_id = item['creator_id']
            slug, price, description, ad_created_date, link, chat_link, photo_link = self.parse_item(item)
            seller_name, location, last_logged_in, seller_registration_date, items_quantity = await self.parse_seller(
                session,
                seller_id)
            check = await self.check_to_send_message(items_quantity, ad_created_date, seller_registration_date)
            if check:
                await self.send_message(slug, price, location, description, ad_created_date, link, chat_link,
                                        photo_link,
                                        seller_name, items_quantity, seller_registration_date, last_logged_in)

    def parse_item(self, item):
        slug = item['title']
        price = item['price_amount']['val'] + " " + self.currency
        description = truncate_string(item['description'])
        ad_created_date = moscow_time(item['first_published_at'], "%Y-%m-%dT%H:%M:%S%z")
        link = f"https://poshmark.{self.url_ending}/listing/{slug} {item['id']}"
        chat_link = link
        photo_link = item['picture_url']
        return slug, price, description, ad_created_date, link, chat_link, photo_link

    async def parse_seller(self, session, id):
        url = f"https://poshmark.{self.url_ending}/vm-rest/users/{id}"
        response = await self.fetch_query(session, url)
        name = response['data']['full_name']
        location = "Пусто"
        try:
            location = response['data']['profile_v2']['city'] + " " + response['data']['profile_v2']['state']
        except Exception as e:
            logging.error("parse seller location", e)
        last_logged_in = response['data']['aggregates']['last_active_date']
        seller_registration_date = moscow_time(response['data']['aggregates']['created_at'], "%Y-%m-%dT%H:%M:%S%z")
        items_quantity = response['data']['aggregates']['total_posts']
        return name, location, last_logged_in, seller_registration_date, items_quantity

    async def check_to_send_message(self, quantity_of_ads, ad_created_date, seller_registration_date):
        if self.quantity_of_ads is not None:
            if self.quantity_of_ads > int(quantity_of_ads):
                return False
        if self.ad_created_date is not None:
            if self.ad_created_date != ad_created_date:
                return False
        if self.seller_registration_date is not None:
            if self.seller_registration_date != seller_registration_date:
                return False
        return True

    async def send_message(self, slug, price, location, description, ad_date_created, link, chat_link, photo_link,
                           seller_name, items_quantity, seller_registration_date, last_logged):
        text = f"🗂 Товар:  {slug}\n" \
               f"💶 Цена:  {price}\n" \
               f"📍 Местоположение товара:  {location}\n" \
               f"📖 Описание:  {description}\n\n" \
               f"🕒 Дата создания объявления:  {ad_date_created}\n" \
               f"🔗 [Ссылка на товар]({link})\n" \
               f"🔗 [Ссылка на чат с продавцом]({chat_link})\n" \
               f"🔗 [Ссылка на фото]({photo_link})\n\n" \
               f"🤵‍♂ Имя продавца:  {seller_name}\n" \
               f"🕒 Дата регистрации продавца:  {seller_registration_date} МСК\n" \
               f"🕒 Был в сети:  {last_logged} МСК\n" \
               f"📂 Кол-во объявления продавца:  {items_quantity}\n"

        if not await self.send_message_with_photo_alternatives(text, [photo_link,
                                                                      "https://upload.wikimedia.org/wikipedia/ru/thumb/a/ac/No_image_available.svg/1200px-No_image_available.svg.png"]):
            pass

    async def send_message_with_photo(self, message, photo_link):
        try:
            button = [
                [
                    Button.text("Остановить парсер", resize=True, single_use=True)
                ]
            ]
            await client_bot.send_message(self.chat_id, message=message, buttons=button, file=photo_link,
                                          link_preview=False,
                                          parse_mode='md')
        except Exception as e:
            return False
        return True

    async def send_message_with_photo_alternatives(self, message, photo_links):
        for photo_link in photo_links:
            if await self.send_message_with_photo(message, photo_link):
                return True
        return False

    async def main(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in self.urls:
                task = asyncio.create_task(self.parse_object(session, url))
                tasks.append(task)
            responses = await asyncio.gather(*tasks)
            return responses


async def run_poshmark(urls, country, quantity_of_ads, seller_registration_date,
                       ad_created_date, chat_id, price_min, price_max):
    parser = Poshmark(urls, country, quantity_of_ads, seller_registration_date,
                      ad_created_date, chat_id, price_min, price_max)
    await parser.main()
    await client_bot.send_message(chat_id, message="✅ Парсер завершен")
