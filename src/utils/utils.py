import random
import string
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import pytz
import requests

from src.utils.constants import depop, grailed, poshmark, schpock, vinted, wallapop


def convert_to_float(number):
    try:
        result = float(number)
        if result > 0:
            return True
        return False
    except Exception as e:
        return False


def btc_to_rub():
    return float(
        requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCRUB"
        ).json()["price"]
    )


def time_ago(timestamp):
    current_time = datetime.utcnow()
    given_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    time_difference = current_time - given_time

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return f"{days} дней, {hours} часов, {minutes} минут назад"


def moscow_time(timestamp, pattern="%Y-%m-%d %H:%M:%S.%f"):
    utc_timezone = pytz.timezone("UTC")
    moscow_timezone = pytz.timezone("Europe/Moscow")
    dt = datetime.strptime(str(timestamp), pattern).replace(tzinfo=utc_timezone)
    moscow_dt = dt.astimezone(moscow_timezone)
    time = moscow_dt.strftime("%Y-%m-%d %H:%M:%S")
    return time


def convert_from_moscow_to_utc(user_time: str):
    msk_tz = pytz.timezone('Europe/Moscow')

    if len(user_time) == 5:
        user_time = datetime.now().strftime('%Y-%m-%d') + " " + user_time

    user_time = datetime.strptime(user_time, '%Y-%m-%d %H:%M')
    user_time = msk_tz.localize(user_time)

    utc_time = user_time.astimezone(pytz.utc)
    return utc_time


def convert_utc_to_moscow(timestamp):
    utc_datetime = datetime.fromtimestamp(timestamp / 1000, timezone.utc)
    moscow_timezone = timezone(timedelta(hours=3))
    moscow_datetime = utc_datetime.astimezone(moscow_timezone)
    date_str = moscow_datetime.strftime("%Y-%m-%d")
    return date_str


def flag(country):
    if country == "AU":
        return "🇦🇺"
    elif country == "DE":
        return "🇩🇪"
    elif country == "US":
        return "🇺🇸"
    elif country == "UK":
        return "🇬🇧"
    elif country == "IT":
        return "🇮🇹"
    elif country == "FR":
        return "🇫🇷"
    elif country == "CA":
        return "🇨🇦"
    elif country == "EU":
        return "🌍"
    elif country == "ASIA":
        return "🌏"
    elif country == "IN":
        return "🇮🇳"
    elif country == "AT":
        return "🇦🇹"
    elif country == "ES":
        return "🇪🇸"
    elif country == "FI":
        return "🇫🇮"
    elif country == "NL":
        return "🇳🇱"
    elif country == "NO":
        return "🇳🇴"
    elif country == "SE":
        return "🇸🇪"
    elif country == "BE":
        return "🇧🇪"
    elif country == "HU":
        return "🇭🇺"
    elif country == "LT":
        return "🇱🇹"
    elif country == "LU":
        return "🇱🇺"
    elif country == "PL":
        return "🇵🇱"
    elif country == "PT":
        return "🇵🇹"
    elif country == "SK":
        return "🇸🇰"


def link_remove_default(link):
    parsed_url = urlparse(link)
    query_params = parse_qs(parsed_url.query)
    if 'q' in query_params:
        return query_params['q'][0]
    return None


def link_remove_price_range(link):
    parsed_url = urlparse(link)
    query_params = parse_qs(parsed_url.query)

    if 'priceMin' in query_params:
        del query_params['priceMin']
    if 'priceMax' in query_params:
        del query_params['priceMax']

    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query))

    return new_url


def truncate_string(string):
    if len(string) > 180:
        truncated_string = string[:180] + "..."
        return truncated_string
    else:
        return string


def description_of_area(subscription):
    if "DEPOP" in subscription:
        return depop
    elif "GRAILED" in subscription:
        return grailed
    elif "POSHMARK" in subscription:
        return poshmark
    elif "SCHPOCK" in subscription:
        return schpock
    elif "VINTED" in subscription:
        return vinted
    elif "WALLAPOP" in subscription:
        return wallapop


def generate_random_string(length):
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string
