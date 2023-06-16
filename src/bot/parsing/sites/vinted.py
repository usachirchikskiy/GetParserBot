class Vinted:
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
