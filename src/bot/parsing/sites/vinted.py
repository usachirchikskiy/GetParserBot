import asyncio
import logging

import aiohttp
from telethon import Button
from telethon.errors import UserIsBlockedError

from src.main import client_bot
from src.utils.utils import truncate_string, moscow_time


class Vinted:
    def __init__(self, urls, location, items_quantity, items_quantity_sold,
                 ad_created_date, seller_rating, chat_id, price_min, price_max):
        self.price_min = price_min
        self.price_max = price_max
        self.location = location
        self.items_quantity = int(items_quantity) if items_quantity != "" else None
        self.items_quantity_sold = int(items_quantity_sold) if items_quantity_sold != "" else None
        self.ad_created_date = ad_created_date if ad_created_date != "" else None
        self.seller_rating = seller_rating if seller_rating != "" else None
        self.urls = urls
        self.chat_id = chat_id
        if self.location == "uk": self.location = "co.uk"
        self.headers = {}

    async def get_headers(self, session):
        async with session.get(f"https://www.vinted.{self.location}") as response:
            _vinted_fr_session = response.cookies['_vinted_fr_session']
            value = _vinted_fr_session.value
            self.headers = {
                "Cookie": f"_vinted_fr_session={value};"
            }

    async def fetch_query_get(self, session, url):
        async with session.get(url, headers=self.headers) as response:
            return await response.json()

    async def parse_object(self, session, query):
        try:
            url = f"https://www.vinted.{self.location}/api/v2/catalog/items?per_page=500&search_text={query}&price_from={self.price_min}" \
                  f"&price_to={self.price_max}&page=1"
            response = await self.fetch_query_get(session, url)
            pages = response['pagination']['total_pages']
            await self.parse_items(session, response['items'])

            for page in range(2, pages + 1):
                response = await self.fetch_query_get(session, url)
                await self.parse_items(session, response['items'])
            await asyncio.sleep(0)
        except asyncio.CancelledError:
            logging.error(f'parse_object Cancelled ERROR')
            raise
        except UserIsBlockedError:
            logging.error(f"parse_object Bot was blocked by the user: {self.chat_id}")
            return
        except Exception as e:
            logging.error(f'parse_object ERROR {e}')
            return

    async def parse_items(self, session, items):
        for item in items:
            id = item['id']
            result = await self.parse_item(session, id)
            check = await self.check_to_send_message(result[-2], result[-3], result[-4], result[4])
            if check:
                await self.send_message(result[0], result[1], result[2], result[3],
                                        result[4], result[5], result[6], result[7],
                                        result[8], result[9], result[10], result[11], result[12])

    async def parse_item(self, session, id):
        url = f"https://www.vinted.{self.location}/api/v2/items/{id}"
        response = await self.fetch_query_get(session, url)
        slug = response["item"]["title"]
        price = str(response["item"]['price']['amount']) + " " + response["item"]["price"]['currency_code']
        location = response["item"]["city"] + "," + response['item']['country']
        description = truncate_string(response["item"]['description'])
        ad_created_date = moscow_time(response["item"]['created_at_ts'], "%Y-%m-%dT%H:%M:%S%z")
        link = f"https://www.vinted.{self.location}/" + response["item"]['path']
        chat_link = link
        photo_link = response["item"]['photos'][0]["url"]
        seller_name = response["item"]['user']["login"]
        seller_rating = response["item"]["user"]['feedback_reputation'] * 5
        items_quantity_sold = response["item"]["user"]['given_item_count']
        items_quantity = response["item"]["user"]['item_count']
        last_logged = moscow_time(response["item"]['user']['last_loged_on_ts'], "%Y-%m-%dT%H:%M:%S%z")
        return slug, price, location, description, ad_created_date, link, chat_link, photo_link, \
               seller_name, seller_rating, items_quantity_sold, items_quantity, last_logged

    async def check_to_send_message(self, items_quantity, items_quantity_sold, rating,
                                    ad_created_date):
        if self.items_quantity is not None:
            if self.items_quantity > int(items_quantity):
                return False
        if self.seller_rating is not None:
            if self.seller_rating > float(rating):
                return False
        if self.ad_created_date is not None:
            if self.ad_created_date != ad_created_date:
                return False
        if self.items_quantity is not None:
            if self.items_quantity > items_quantity:
                return False
        if self.items_quantity_sold is not None:
            if self.items_quantity_sold > items_quantity_sold:
                return False
        return True

    async def send_message(self, slug, price, location, description, ad_date_created, link, chat_link, photo_link,
                           seller_name, seller_rating, quantity_sold_items, items_quantity, last_logged):
        text = f"🗂 Товар:  {slug}\n" \
               f"💶 Цена:  {price}\n" \
               f"📍 Местоположение товара:  {location}\n" \
               f"📖 Описание:  {description}\n\n" \
               f"🕒 Дата создания объявления:  {ad_date_created}\n" \
               f"🔗 [Ссылка на товар]({link})\n" \
               f"🔗 [Ссылка на чат с продавцом]({chat_link})\n" \
               f"🔗 [Ссылка на фото]({photo_link})\n\n" \
               f"🤵‍♂ Имя продавца:  {seller_name}\n" \
               f"⭐ Рейтинг продавца:  {seller_rating}\n" \
               f"📂 Кол-во проданных товаров продавца:  {quantity_sold_items}\n" \
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
            await self.get_headers(session)
            tasks = []
            for url in self.urls:
                task = asyncio.create_task(self.parse_object(session, url))
                tasks.append(task)
            responses = await asyncio.gather(*tasks)
            return responses


async def run_vinted(urls, location, items_quantity, items_quantity_sold,
                 ad_created_date, seller_rating, chat_id, price_min, price_max):
    parser = Vinted(urls, location, items_quantity, items_quantity_sold,
                 ad_created_date, seller_rating, chat_id, price_min, price_max)
    await parser.main()
    await client_bot.send_message(chat_id, message="✅ Парсер завершен")