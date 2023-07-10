import asyncio
import json
import logging
from urllib.parse import quote

import aiohttp
from telethon import Button
from telethon.errors import UserIsBlockedError

from src.main import client_bot
from src.utils.utils import truncate_string, convert_utc_to_moscow


# Todo shpock_sid

class Schpock:
    def __init__(self, urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                 ad_created_date, seller_rating, chat_id, price_min=0, price_max=200000):
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
        self.schpock_url = "https://www.shpock.com/graphql"
        self.headers = {
            'Content-Type': 'application/json',
            'Cookie': 'shpock_sid=JNZxYXMhw3e45sMFVZYdnMiN2myuKDJG5yYYbNVX648c5a5a;'
        }

    def get_lat_lng(self):
        if self.location == "at":
            return 48.2083537, 16.3725042
        elif self.location == "uk":
            return 51.5073359, 0.12765
        elif self.location == "de":
            return 52.5170365, 13.3888599
        elif self.location == "it":
            return 41.8933203, 12.4829321
        elif self.location == "se":
            return 59.32533135, 18.100340839058855
        elif self.location == "no":
            return 64.5731537, 11.52803643954819
        elif self.location == "fi":
            return 60.1674881, 24.9427473
        elif self.location == "es":  # spain
            return 39.3260685, -4.8379791
        elif self.location == "hu":
            return 47.4979937, 19.0403594
        elif self.location == "fr":
            return 48.8534951, 2.3483915

    def change_header(self):
        pass

    def get_post_data_item(self, id):
        return json.dumps({
            "operationName": "ItemPage",
            "variables": {
                "id": id
            },
            "query": "query ItemPage($id: ID!) {\n  item(id: $id) {\n    status\n    result {\n      __typename\n      id\n      title\n      description\n      path\n      locality\n      price\n      originalPrice\n      currency\n      media {\n        id\n        width\n        height\n        title\n        __typename\n      }\n      location {\n        latitude\n        longitude\n        __typename\n      }\n      startDate\n      modifiedDate\n      expirationDate\n      dateSold\n      dealState\n      distance\n      user {\n        id\n        name\n        avatar {\n          id\n          width\n          height\n          isDefault\n          __typename\n        }\n        language\n        locale\n        signupDate\n        proSellerVertical\n        avgRating\n        numRatings\n        numItemsSold\n        numItemsBought\n        numItemsSelling\n        isProSeller\n        username\n        isTrustedSeller\n        __typename\n      }\n      buyer {\n        id\n        name\n        __typename\n      }\n      numLikes\n      ...itemTagsFragment\n      category\n      extraProperties {\n        name\n        value\n        label\n        valueLabel\n        __typename\n      }\n      od\n      metadata {\n        displayName\n        displayValue\n        __typename\n      }\n      activityGroup {\n        id\n        kind\n        interactionType\n        __typename\n      }\n      latestActivities {\n        __typename\n        ... on Activity {\n          id\n          kind\n          activityGroupId\n          interactionType\n          date\n          actor {\n            id\n            name\n            avatar {\n              id\n              __typename\n            }\n            __typename\n          }\n          target {\n            id\n            name\n            avatar {\n              id\n              __typename\n            }\n            __typename\n          }\n          subject\n          iconId\n          summary {\n            title\n            body\n            __typename\n          }\n          __typename\n        }\n        ... on MakeOfferActivity {\n          message\n          __typename\n        }\n        ... on AcceptOfferActivity {\n          message\n          __typename\n        }\n        ... on ChatActivity {\n          message\n          __typename\n        }\n        ... on PrivateMessageActivity {\n          message\n          __typename\n        }\n      }\n      ...itemQuestions\n      allowedActivities {\n        canDelistItem\n        canMarkAsSoldElsewhere\n        canEdit\n        editableFields\n        canAddItemToWatchList\n        canDialNumber\n        canReportItem\n        canBuyNow\n        __typename\n      }\n      paymentOptions {\n        isBuyNow\n        __typename\n      }\n      showPaymentSummary\n      paymentSummary {\n        entryId\n        price\n        formattedPrice\n        label\n        __typename\n      }\n      parcel {\n        shippingPrice\n        size\n        isShippingPriceAssumed\n        __typename\n      }\n      reactivationStatus\n      watchlistToggle\n      adKeywords\n      canonicalURL\n      businessBadges {\n        label\n        iconId\n        iconUrl\n        article\n        __typename\n      }\n    }\n    __typename\n  }\n}\n\nfragment itemQuestions on Item {\n  id\n  allowedActivities {\n    canAskQuestions\n    answerQuestions\n    removeQuestions\n    removeAnswers\n    __typename\n  }\n  countQuestions\n  countAnswers\n  questions {\n    id\n    date\n    user {\n      id\n      name\n      avatar {\n        id\n        __typename\n      }\n      isProSeller\n      numItemsSelling\n      __typename\n    }\n    message\n    answers {\n      id\n      date\n      user {\n        id\n        name\n        avatar {\n          id\n          __typename\n        }\n        isProSeller\n        numItemsSelling\n        __typename\n      }\n      message\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment itemTagsFragment on Item {\n  isNew\n  isSold\n  isFree\n  isOnSale\n  isLiked\n  isWatched\n  isBoosted\n  isShippable\n  isExpired\n  __typename\n}\n"
        })

    def get_post_data(self, query, lat, lng, offset):
        post_data = {
            "operationName": "ItemSearch",
            "variables": {
                "trackingSource": "Search",
                "pagination": {
                    "offset": offset
                },
                "serializedFilters": f'{{"q":"{query}","price":{{"from":{self.price_min},"to":{self.price_max}}},"distance":{{"location":{{"lat":{lat},"lng":{lng}}}}}}}'
            },
            "query": "query ItemSearch($serializedFilters: String, $pagination: Pagination, $trackingSource: TrackingSource!) {\n  itemSearch(\n    serializedFilters: $serializedFilters\n    pagination: $pagination\n    trackingSource: $trackingSource\n  ) {\n    __typename\n    od\n    offset\n    limit\n    count\n    total\n    adKeywords\n    locality\n    spotlightCarousel {\n      ...carouselSummaryFragment\n      __typename\n    }\n    itemResults {\n      distanceGroup\n      items {\n        ...summaryFragment\n        __typename\n      }\n      __typename\n    }\n    filters {\n      __typename\n      kind\n      key\n      triggerLabel\n      serializedValue\n      status\n      ... on CascaderFilter {\n        dataSourceKind\n        __typename\n      }\n      ... on SingleSelectListFilter {\n        title\n        options {\n          __typename\n          label\n          subLabel\n          badgeLabel\n          serializedValue\n        }\n        defaultSerializedValue\n        __typename\n      }\n      ... on MultiSelectListFilter {\n        title\n        submitLabel\n        options {\n          __typename\n          label\n          subLabel\n          badgeLabel\n          serializedValue\n        }\n        __typename\n      }\n      ... on SearchableMultiSelectListFilter {\n        title\n        submitLabel\n        searchEndpoint\n        __typename\n      }\n      ... on RangeFilter {\n        title\n        __typename\n      }\n      ... on LegacyPriceFilter {\n        title\n        __typename\n      }\n      ... on LegacyLocationFilter {\n        title\n        __typename\n      }\n      ... on RadioToggleFilter {\n        options {\n          __typename\n          label\n          value\n        }\n        defaultSerializedValue\n        __typename\n      }\n    }\n    savedSearchProposal {\n      isAlreadySaved\n      candidate {\n        id\n        name\n        keyword\n        serializedFilters\n        isNotificationChannelOn\n        isEmailChannelOn\n        displayedFilters {\n          name\n          value\n          format\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n  }\n}\n\nfragment summaryFragment on Summary {\n  __typename\n  ... on ItemSummary {\n    ...itemSummaryFragment\n    __typename\n  }\n  ... on ShopSummary {\n    ...shopSummaryFragment\n    __typename\n  }\n  ... on HeaderSummary {\n    title\n    subtitle\n    __typename\n  }\n}\n\nfragment itemSummaryFragment on ItemSummary {\n  id\n  title\n  media {\n    id\n    width\n    height\n    title\n    __typename\n  }\n  description\n  path\n  distance\n  distanceUnit\n  locality\n  price\n  originalPrice\n  currency\n  watchlistToggle\n  ...itemSummaryTagsFragment\n  canonicalURL\n  __typename\n}\n\nfragment itemSummaryTagsFragment on ItemSummary {\n  isNew\n  isSold\n  isFree\n  isOnSale\n  isLiked\n  isBoosted\n  isShippable\n  isExpired\n  __typename\n}\n\nfragment shopSummaryFragment on ShopSummary {\n  __typename\n  id\n  name\n  avatar {\n    id\n    __typename\n  }\n  media {\n    id\n    __typename\n  }\n  itemCount\n}\n\nfragment carouselSummaryFragment on CarouselSummary {\n  __typename\n  label\n  group\n  items {\n    id\n    title\n    description\n    media {\n      id\n      width\n      height\n      title\n      __typename\n    }\n    path\n    price\n    originalPrice\n    currency\n    watchlistToggle\n    ...itemSummaryTagsFragment\n    canonicalURL\n    __typename\n  }\n}\n"
        }
        return json.dumps(post_data)

    async def fetch_query_get(self, session, url):
        async with session.get(url) as response:
            return await response.json()

    async def fetch_query_post(self, session, data):
        async with session.post(self.schpock_url, data=data, headers=self.headers) as response:
            return await response.json()

    async def parse_object(self, session, query):
        try:
            offset = 0
            lat_lng = self.get_lat_lng()
            post_data = self.get_post_data(query, lat_lng[0], lat_lng[1], offset)
            response = await self.fetch_query_post(session, post_data)
            count = response['data']["itemSearch"]["count"]
            await self.parse_items(session, response["data"]["itemSearch"]["itemResults"][0]["items"])
            while count == 30:
                offset = offset + 30
                post_data = self.get_post_data(query, lat_lng[0], lat_lng[1], offset)
                response = await self.fetch_query_post(session, post_data)
                # if 'data' in response:
                count = response['data']["itemSearch"]["count"]
                await self.parse_items(session, response["data"]["itemSearch"]["itemResults"][0]["items"])
                # elif 'errors' in response:
                # change_header()
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
            check = await self.check_to_send_message(result[-2], result[-3], result[-1], result[-4], result[4])
            if check:
                await self.send_message(result[0], result[1], result[2], result[3],
                                        result[4], result[5], result[6], result[7],
                                        result[8], result[9], result[10], result[11], result[12])

    async def parse_item(self, session, id):
        post_data = self.get_post_data_item(id)
        response = await self.fetch_query_post(session, post_data)
        slug = response["data"]["item"]["result"]["title"]
        price = str(response['data']["item"]["result"]['price']) + " " + response['data']["item"]["result"]['currency']
        location = response['data']["item"]["result"]['locality']
        description = truncate_string(response['data']["item"]["result"]['description'])
        ad_created_date = convert_utc_to_moscow(response['data']["item"]["result"]['startDate'])
        link = "https://www.schpock.com/" + response['data']["item"]["result"]['path']
        chat_link = link
        photo_link = f'https://m1.secondhandapp.at/2.0/{response["data"]["item"]["result"]["media"][0]["id"]}?height=1024&width=1024'
        seller_name = response["data"]["item"]["result"]["user"]["name"]
        seller_rating = response["data"]["item"]["result"]["user"]['avgRating']
        items_quantity_sold = response["data"]["item"]["result"]["user"]['numItemsSold']
        items_quantity = response["data"]["item"]["result"]["user"]['numItemsSold'] + \
                         response["data"]["item"]["result"]["user"]['numItemsSelling']
        seller_registration_date = convert_utc_to_moscow(response["data"]["item"]["result"]["user"]['signupDate'])
        return slug, price, location, description, ad_created_date, link, chat_link, photo_link, \
               seller_name, seller_rating, items_quantity_sold, items_quantity, seller_registration_date

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


async def run_schpock(urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                      ad_created_date, seller_rating, chat_id, price_min, price_max):
    parser = Schpock(urls, location, items_quantity, items_quantity_sold, seller_registration_date,
                     ad_created_date, seller_rating, chat_id, price_min, price_max)
    await client_bot.send_message(chat_id,
                                  message="✅ Парсер запущен, поиск может занять некоторое время, пожалуйста ожидайте.\n\nДля остановки парсера введите: **Остановить парсер**")
    await parser.main()
    await client_bot.send_message(chat_id, message="✅ Парсер завершен")
