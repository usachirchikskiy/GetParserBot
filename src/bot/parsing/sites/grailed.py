import asyncio
import json

import aiohttp
from telethon import Button

from src.main import client_bot
from src.utils.utils import moscow_time, truncate_string


class Grailed:

    def __init__(self, urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                 ad_created_date, seller_rating, chat_id, price_min=0, price_max=200000):
        self.price_min = price_min
        self.price_max = price_max
        self.location = location
        self.items_quantity = int(items_quantity) if items_quantity != "" else None
        self.items_quantity_sold = int(items_quantity_sold) if items_quantity_sold != "" else None
        self.seller_registration_date = seller_registration_date if seller_registration_date != "" else None
        self.ad_created_date = ad_created_date if ad_created_date != "" else None
        self.seller_rating = seller_rating if seller_rating != "" else None
        self.urls = urls
        self.chat_id = chat_id
        self.grailed_url = "https://mnrwefss2q-2.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.14.3)%3B%20Browser%3B%20JS%20Helper%20(3.11.3)%3B%20react%20(18.2.0)%3B%20react-instantsearch%20(6.39.1)"
        self.headers = {
            'X-Algolia-Api-Key': 'bc9ee1c014521ccf312525a4ef324a16',
            'X-Algolia-Application-Id': 'MNRWEFSS2Q',
            'Content-Type': 'application/json'
        }

    async def fetch_query_get(self, session, url):
        async with session.get(url) as response:
            return await response.json()

    async def fetch_query_post(self, session, data):
        async with session.post(self.grailed_url, data=data, headers=self.headers) as response:
            return await response.json()

    async def parse_object(self, session, query):
        post_data = self.get_post_data(query, 0)
        response = await self.fetch_query_post(session, post_data)
        number_of_pages = response['results'][0]["nbPages"]
        await self.parse_items(session, response['results'][0]['hits'])
        if number_of_pages > 1:
            for i in range(1, number_of_pages):
                post_data = self.get_post_data(query, i)
                response = await self.fetch_query_post(session, post_data)
                await self.parse_items(session, response['results'][0]['hits'])

    async def parse_items(self, session, items):
        for item in items:
            id = item['id']
            result = await self.parse_item(session, id)
            check = await self.check_to_send_message(result[-2], result[-3], result[-1], result[-4], result[4])
            if check:
                await self.send_message(result[0], result[1], result[2], result[3],
                                        result[4], result[5], result[6], result[7],
                                        result[8], result[9], result[10], result[11], result[12])

    async def parse_item(self, session, id):
        url = f"https://www.grailed.com/api/listings/{id}"
        response = await self.fetch_query_get(session, url)
        slug = response['data']['title']
        price = str(response['data']['price']) + " " + response['data']['currency']
        location = response['data']['seller']['location']
        description = truncate_string(response['data']['description'])
        ad_created_date_utc = response['data']['created_at']
        ad_created_date = moscow_time(ad_created_date_utc, "%Y-%m-%dT%H:%M:%S.%fZ")
        link = "https://www.grailed.com" + response['data']['pretty_path']
        chat_link = link
        photo_link = response['data']['photos'][0]['url']
        seller_name = response['data']['seller']['username']
        seller_rating = response['data']['seller']['seller_score']['rating_average']
        items_quantity_sold = response['data']['seller']['total_bought_and_sold']
        items_quantity = response['data']['seller']['listings_for_sale_count']
        seller_registration_date = moscow_time(response['data']['seller']['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        return slug, price, location, description, ad_created_date, link, chat_link, photo_link, \
               seller_name, seller_rating, items_quantity_sold, items_quantity, seller_registration_date

    async def check_to_send_message(self, items_quantity, items_quantity_sold, seller_registration_date, rating,
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
        if self.seller_registration_date is not None:
            if self.seller_registration_date != seller_registration_date:
                return False
        return True

    async def send_message(self, slug, price, location, description, ad_date_created, link, chat_link, photo_link,
                           seller_name, seller_rating, quantity_sold_items, items_quantity, seller_registration_date):
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

    def get_post_data(self, query, page):
        post_data = {
            "requests": [
                {
                    "indexName": "Listing_production",
                    "params": f'analytics=true&clickAnalytics=true&enableABTest=true&enablePersonalization=true'
                              f'&facetFilters=[["location:{self.location}"]]&facets=["department","category_path",'
                              '"category_size","designers.name","price_i","condition","location","badges",'
                              '"strata"]&filters=&getRankingInfo=true&highlightPostTag=</ais-highlight-0000000000'
                              '>&highlightPreTag=<ais-highlight-0000000000>&hitsPerPage=250&maxValuesPerFacet=100'
                              f'&numericFilters=["price_i>={self.price_min}",'
                              f'"price_i<={self.price_max}"]&page={page}&personalizationImpact=99&query={query}&tagFilters'
                              '=&userToken=535920 '
                }
            ]
        }
        return json.dumps(post_data)

    async def main(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in self.urls:
                task = asyncio.create_task(self.parse_object(session, url))
                tasks.append(task)
            responses = await asyncio.gather(*tasks)
            return responses
