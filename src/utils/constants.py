import asyncio
import math

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import STATIC, DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

jobs = []
parsing_tasks = {}

semaphore = asyncio.Semaphore(30)
jobstores = {
    'default': SQLAlchemyJobStore(url=f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
scheduler.start()

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

media = STATIC + "get_parser.jpg"
tech_support_link = "https://t.me/Jikolav"
percentage_string = "5 %"
percentage_number = 0.05
admin_id = [1574853044, 5497962695]
bot_token = "6396996150:AAGf10I36Pmgp3l46L_INqHvANp8vfb6dFE"
api_id = 16819926
api_hash = "65788ccadd6ccbd8695f19710b41a2fd"
user_bitpapa = "user_bitpapa"
