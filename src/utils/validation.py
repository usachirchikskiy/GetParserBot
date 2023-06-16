import re
from datetime import datetime
from urllib.parse import urlparse


class Validation:
    incorrect_input_words_links = "⚠️Неверный ввод\nВведите ссылки на категории или ключевые слова через запятую"
    incorrect_input_price_range = "⚠️Неверный ввод\nВведите диапазон цены товара:\nПример: 100-80000"
    incorrect_input_quantity = "⚠️Неверный ввод\nВведите целое число > 0"
    incorrect_input_date = "⚠️Неверный ввод\nПример ввода: (год-месяц-число) 2015-12-24"
    incorrect_input_yes_or_no = "⚠️Неверный ввод\nВведите да\нет"

    @staticmethod
    def is_link(link):
        pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        if pattern.match(link):
            return True
        else:
            return False

    @staticmethod
    def check_url_contains_domain(urls, domain):
        is_url = False
        is_not_url = False
        for url in urls:
            if Validation.is_link(url):
                parsed_url = urlparse(url)
                if domain in parsed_url.netloc:
                    is_url = True
                else:
                    is_url = False
            else:
                is_not_url = True
            if is_url and is_not_url:
                return False
        return is_url or is_not_url

    @staticmethod
    def validate_price_range(price_range):
        if price_range == "Не использовать фильтр": return True
        pattern = r'^\d+-\d+$'  # Регулярное выражение для проверки формата диапазона цены
        if re.match(pattern, price_range):
            return True
        else:
            return False

    @staticmethod
    def validate_date(date_str):
        if date_str == "Не использовать фильтр": return True
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_yes_no(msg):
        if msg.lower() == "нет" or msg.lower() == "да":
            return True
        return False

    @staticmethod
    def validate_positive_integer(number, rating=None):
        if number == "Не использовать фильтр": return True
        try:
            number = int(number)
            if number > 0:
                if rating:
                    if number < 6:
                        return True
                    return False
                else:
                    return True
            else:
                return False
        except ValueError:
            return False
