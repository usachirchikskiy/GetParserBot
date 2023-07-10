import asyncio
import logging
from urllib.parse import quote

import aiohttp
from telethon.errors import UserIsBlockedError

from src.main import client_bot
from src.utils.utils import convert_utc_to_moscow, truncate_string


class WallaPop:
    def __init__(self, urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                 ad_created_date, seller_rating, chat_id, price_min, price_max):
        self.price_min = price_min
        self.price_max = price_max
        self.location = location
        self.items_quantity = int(items_quantity) if items_quantity != "" else None
        self.items_quantity_sold = int(items_quantity_sold) if items_quantity_sold != "" else None
        self.seller_registration_date = seller_registration_date if seller_registration_date != "" else None
        self.ad_created_date = ad_created_date if ad_created_date != "" else None
        self.seller_rating = int(seller_rating) if seller_rating != "" else None
        self.urls = urls
        self.chat_id = chat_id

    def get_lat_lng(self):
        if self.location == "es":
            return 40.41956, -3.69196
        elif self.location == "uk" or self.location == "fr":
            return 51.509865, 0.118092
        elif self.location == "it":
            return 41.8905, 12.4942
        elif self.location == "pt":
            return 38.736946, -9.142685

    async def fetch_query_get(self, session, url):
        async with session.get(url) as response:
            return await response.json()

    async def parse_object(self, session, query):
        try:
            lat_lng = self.get_lat_lng()
            start = 0
            url = f"https://api.wallapop.com/api/v3/general/search?filters_source=search_box&keywords={query}&longitude={lat_lng[1]}" \
                  f"&latitude={lat_lng[0]}&start={start}&min_sale_price={self.price_min}&max_sale_price={self.price_max}"
            response = await self.fetch_query_get(session, url)
            count = len(response['search_objects'])
            await self.parse_items(session, response["search_objects"])
            while count != 0:
                start = start + 40
                url = f"https://api.wallapop.com/api/v3/general/search?filters_source=search_box&keywords={query}&longitude={lat_lng[1]}" \
                      f"&latitude={lat_lng[0]}&start={start}&min_sale_price={self.price_min}&max_sale_price={self.price_max}"
                response = await self.fetch_query_get(session, url)
                count = len(response['search_objects'])
                await self.parse_items(session, response["search_objects"])
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
            seller_id = item['user']['id']
            seller = await self.parse_seller(session, seller_id)
            slug = item['title']
            price = str(item['price']) + " " + item['currency']
            location = item['location']['city']
            description = truncate_string(item['description'])
            ad_created_date = convert_utc_to_moscow(item['creation_date'])
            link = f"https://{self.location}.wallapop.com/item/{item['web_slug']}"
            chat_link = link
            photo_link = item['images'][0]['medium']
            check = await self.check_to_send_message(seller[-2], seller[-3], seller[-1], seller[1], ad_created_date)
            if check:
                await self.send_message(slug, price, location, description, ad_created_date, link, chat_link,
                                        photo_link,
                                        seller[0], seller[1], seller[2], seller[3],
                                        seller[4])

    async def check_to_send_message(self, items_quantity, items_quantity_sold, seller_registration_date, rating,
                                    ad_created_date):
        if self.items_quantity is not None:
            if self.items_quantity < int(items_quantity):
                return False
        if self.seller_rating is not None and rating is not None:
            if self.seller_rating < float(rating):
                return False
        if self.ad_created_date is not None:
            if self.ad_created_date != ad_created_date:
                return False
        if self.items_quantity is not None:
            if self.items_quantity < items_quantity:
                return False
        if self.items_quantity_sold is not None:
            if self.items_quantity_sold < items_quantity_sold:
                return False
        if self.seller_registration_date is not None:
            if self.seller_registration_date != seller_registration_date:
                return False
        return True

    async def send_message(self, slug, price, location, description, ad_date_created, link, chat_link, photo_link,
                           seller_name, seller_rating, quantity_sold_items, items_quantity, seller_registration_date):
        if seller_rating is None:
            seller_rating = 0
        link = quote(link, safe=':/')
        chat_link = quote(chat_link, safe=':/')

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
               f"🕒 Дата регистрации продавца:  {seller_registration_date} МСК\n" \
               f"📂 Кол-во объявления продавца:  {items_quantity}\n"

        if not await self.send_message_with_photo_alternatives(text, [photo_link,
                                                                      "https://upload.wikimedia.org/wikipedia/ru/thumb/a/ac/No_image_available.svg/1200px-No_image_available.svg.png"]):
            pass

    async def parse_seller(self, session, seller_id):
        url = f"https://api.wallapop.com/api/v3/users/{seller_id}"
        url_stats = f"https://api.wallapop.com/api/v3/users/{seller_id}/stats"
        seller = await self.fetch_query_get(session, url)
        seller_stats = await self.fetch_query_get(session, url_stats)
        seller_name = seller['micro_name']
        seller_rating = seller_stats['ratings'][0]['value']
        items_quantity_sold = seller_stats['counters'][4]['value']
        items_quantity = seller_stats['counters'][0]['value']
        seller_registration_date = convert_utc_to_moscow(seller['register_date'])
        return seller_name, seller_rating, items_quantity_sold, items_quantity, seller_registration_date

    async def send_message_with_photo(self, message, photo_link):
        try:
            # button = [
            #     [
            #         Button.text("Остановить парсер", resize=True, single_use=True)
            #     ]
            # ]
            await client_bot.send_message(self.chat_id, message=message,
                                          # buttons=button,
                                          file=photo_link,
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


async def run_wallapop(urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                       ad_created_date, seller_rating, chat_id, price_min, price_max):
    parser = WallaPop(urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                      ad_created_date, seller_rating, chat_id, price_min, price_max)
    await client_bot.send_message(chat_id,
                                  message="✅ Парсер запущен, поиск может занять некоторое время, пожалуйста ожидайте.\n\nДля остановки парсера введите: **Остановить парсер**")
    await parser.main()
    await client_bot.send_message(chat_id, message="✅ Парсер завершен")
