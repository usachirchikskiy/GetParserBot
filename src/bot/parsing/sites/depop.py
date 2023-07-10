import asyncio
import logging
from urllib.parse import quote

import aiohttp
from telethon import Button
from telethon.errors import UserIsBlockedError

from src.main import client_bot
from src.utils.utils import time_ago, link_remove_default, link_remove_price_range, truncate_string
from src.utils.validation import Validation


class DepopParser:
    def __init__(self, urls, price_min, price_max,
                 quantity_of_ads, seller_rating,
                 ad_created_date, country,
                 chat_id):
        self.price_min = price_min if price_min != "" else None
        self.price_max = price_max if price_max != "" else None
        self.quantity_of_ads = int(quantity_of_ads) if quantity_of_ads != "" else None
        self.seller_rating = int(seller_rating) if seller_rating != "" else None
        self.ad_created_date = ad_created_date if ad_created_date != "" else None
        self.country = country
        self.currency = self.get_currency(country)
        self.chat_id = chat_id
        self.urls = self.handle_urls(urls)

    def get_currency(self, country):
        if country == "au":
            return "AUD"
        elif country == "de" or country == "fr" or country == "it":
            return "EUR"
        elif country == "gb":
            return "GBP"
        elif country == "us":
            return "USD"

    def handle_urls(self, urls):
        urls_list = []
        for url in urls:
            what = url
            if Validation.is_link(url):
                if link_remove_default(url):
                    what = link_remove_default(url)

            new_url = f"https://webapi.depop.com/api/v2/search/products/?what={what}&itemsPerPage=200&country={self.country}&currency={self.currency}"
            if self.price_min and self.price_max:
                new_url = link_remove_price_range(
                    new_url) + "&priceMin=" + self.price_min + "&priceMax=" + self.price_max
            urls_list.append(new_url)
        return urls_list

    async def fetch_query(self, session, url):
        async with session.get(url) as response:
            return await response.json()

    async def parse_object(self, session, url):
        try:
            while True:
                response = await self.fetch_query(session, url)
                has_more = response['meta']['hasMore']
                items = response['products']
                await self.parse_items(session, items)
                if has_more:
                    cursor = response['meta']['cursor']
                    url = url + "&cursor=" + cursor
                else:
                    break
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
            slug = item['slug']  # item title
            link = "https://www.depop.com/products/" + slug
            photo_link = item['preview']['640']
            photo_link_480 = item['preview']['480']
            photo_link_320 = item['preview']['320']
            item_url = f"https://webapi.depop.com/api/v2/product/{slug}"
            result = await self.parse_item(session, item_url)
            description = truncate_string(result[2])
            seller_url = f"https://webapi.depop.com/api/v1/shop/{result[4]}"
            seller = await self.parse_seller(session, seller_url)
            check = await self.check_to_send_message(seller[3], seller[2].replace("/5", ""), result[3])
            if check:
                await self.send_message(slug, result[0], result[1], description, result[3], link, result[5], photo_link,
                                        seller[0], seller[1], seller[2], seller[3], photo_link_480, photo_link_320)

    async def parse_item(self, session, url):
        try:
            response = await self.fetch_query(session, url)
            currency = response['price']['currencyName']
            price = f"{response['price']['priceAmount']} {currency}"
            address = response['address']
            description = response['description']
            date_updated = time_ago(response['dateUpdated'])
            seller = response['seller']['username']
            chat_link = f"https://www.depop.com/messages/create?userId={response['seller']['id']}&productId={response['id']}"
            return price, address, description, date_updated, seller, chat_link
        except Exception as e:
            logging.error(f'parse_item ERROR {e}')

    async def parse_seller(self, session, url):
        try:
            response = await self.fetch_query(session, url)
            name = response['first_name'] + " " + response["last_name"]
            date_updated = time_ago(response['last_seen'])
            rating = f"{response['reviews_rating']}/5"
            items_sold = response['items_sold']
            return name, date_updated, rating, items_sold
        except Exception as e:
            logging.error(f'parse_seller ERROR {e}')

    async def check_to_send_message(self, quantity_of_ads, rating, ad_created_date):
        if self.quantity_of_ads is not None:
            if self.quantity_of_ads < int(quantity_of_ads):
                return False
        if self.seller_rating is not None and rating is not None:
            if self.seller_rating < float(rating):
                return False
        if self.ad_created_date is not None:
            if self.ad_created_date != ad_created_date:
                return False
        return True

    async def send_message(self, slug, price, location, description, ad_date_created, link, chat_link, photo_link,
                           seller_name, seller_last_seen, seller_rating, quantity_sold_items, photo_link_480,
                           photo_link_320):
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
               f"🔔 Был(-а) в сети:  {seller_last_seen} МСК\n" \
               f"⭐ Рейтинг продавца:  {seller_rating}\n" \
               f"📂 Кол-во проданных товаров продавца:  {quantity_sold_items}"

        if not await self.send_message_with_photo_alternatives(text, [photo_link, photo_link_480, photo_link_320]):
            pass

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


async def run_depop(urls, price_min, price_max,
                    quantity_of_ads, seller_rating,
                    ad_created_date, country,
                    chat_id):
    parser = DepopParser(urls, price_min, price_max,
                         quantity_of_ads, seller_rating,
                         ad_created_date, country,
                         chat_id)
    await client_bot.send_message(chat_id,
                                  message="✅ Парсер запущен, поиск может занять некоторое время, пожалуйста ожидайте.\n\nДля остановки парсера введите: **Остановить парсер**")
    await parser.main()
    await client_bot.send_message(chat_id, message="✅ Парсер завершен")
