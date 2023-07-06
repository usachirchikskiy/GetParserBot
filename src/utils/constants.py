import math

from src.config import STATIC

parsing_tasks = {}

media = STATIC + "get_parser.jpg"

sites = [
    ["🇦🇺 DEPOP.AU", "🇩🇪 DEPOP.DE"],
    ["🇺🇸 DEPOP.US", "🇬🇧 DEPOP.UK"],
    ["🇮🇹 DEPOP.IT", "🇫🇷 DEPOP.FR"],
    ["🇺🇸 GRAILED.US", "🇨🇦 GRAILED.CA"],
    ["🇬🇧 GRAILED.UK", "🌍 GRAILED.EU"],
    ["🌏 GRAILED.ASIA", "🇦🇺 GRAILED.AU/NZ"],
    ["🇦🇺 POSHMARK.AU", "🇨🇦 POSHMARK.CA"],
    # next
    ["🇪🇸 WALLAPOP.ES", "🇫🇷 WALLAPOP.FR"],
    ["🇮🇹 WALLAPOP.IT", "🇵🇹 WALLAPOP.PT"],
    ["🇬🇧 WALLAPOP.UK", "🇺🇸 POSHMARK.US"],
    ["🇦🇹 SCHPOCK.AT", "🇩🇪 SCHPOCK.DE"],
    ["🇪🇸 SCHPOCK.ES", "🇫🇮 SCHPOCK.FI"],
    ["🇫🇷 SCHPOCK.FR", "🇮🇹 SCHPOCK.IT"],
    ["🇳🇱 SCHPOCK.NL", "🇳🇴 SCHPOCK.NO"],
    # next
    ["🇸🇪 SCHPOCK.SE", "🇬🇧 SCHPOCK.UK"],
    ["🇺🇸 SCHPOCK.US", "🇦🇹 VINTED.AT"],
    ["🇧🇪 VINTED.BE", "🇺🇸 VINTED.COM"],
    ["🇨🇿 VINTED.CZ", "🇩🇪 VINTED.DE"],
    ["🇪🇸 VINTED.ES", "🇫🇷 VINTED.FR"],
    ["🇭🇺 VINTED.HU", "🇮🇹 VINTED.IT"],
    ["🇱🇹 VINTED.LT", "🇱🇺 VINTED.LU"],
    # next
    ["🇳🇱 VINTED.NL", "🇵🇱 VINTED.PL"],
    ["🇵🇹 VINTED.PT", "🇸🇪 VINTED.SE"],
    ["🇸🇰 VINTED.SK", "🇬🇧 VINTED.UK"]
]

total_pages = math.ceil(len(sites) / 7)

depop = '''
▶️ Особенности площадки: Нет номеров телефона\n
▶️ Фильтры площадки:
— Диапазон цены
— Кол-во проданных товаров
— Дата создания объявления
— Рейтинг продавца
'''

grailed = '''
▶️ Особенности площадки: Нет номеров телефона\n
▶️ Фильтры площадки:
— Диапазон цены
— Кол-во объявлений продавца
— Кол-во проданных товаров
— Дата регистрации продавца
— Дата создания объявления
— Рейтинг продавца
'''

poshmark = '''
▶️ Особенности площадки: Нет номеров телефона\n
▶️ Фильтры площадки:
— Диапазон цены
— Кол-во объявлений продавца
— Дата регистрации продавца
— Дата создания объявления
'''

schpock = '''
▶️ Особенности площадки: Нет номеров телефона\n
▶️ Фильтры площадки:
— Диапазон цены
— Кол-во объявлений продавца
— Кол-во проданных товаров
— Дата регистрации продавца
— Дата создания объявления
— Рейтинг продавца
'''

vinted = '''
▶️ Особенности площадки: Нет номеров телефона\n
▶️ Фильтры площадки:
— Диапазон цены
— Кол-во объявлений продавца
— Кол-во проданных товаров
— Дата создания объявления
— Рейтинг продавца
'''

wallapop = '''
▶️ Особенности площадки: Нет номеров телефона\n
▶️ Фильтры площадки:
— Диапазон цены
— Кол-во объявлений продавца
— Кол-во проданных товаров
— Дата регистрации продавца
— Дата создания объявления
— Рейтинг продавца
'''

tech_support_link = "https://t.me/Jikolav"
percentage_string = "5 %"
percentage_number = 0.05
admin_id = [1574853044, 5497962695]
