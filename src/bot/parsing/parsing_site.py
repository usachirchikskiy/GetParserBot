import json

from telethon import Button, events

from src.bot.parsing.parsing_presets import presets
from src.bot.parsing.sites.runner import run_parsing
from src.database.dao.Associations import UserSubscriptionDao, UserFilterSubscriptionDao
from src.database.dao.FilterDao import FilterDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.database.dao.UserDao import UserDao
from src.main import client_bot
from src.utils.constants import depop_url, media
from src.utils.utils import flag, moscow_time, get_currency


def parsing_site_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action'].split(" ")[0]
        return action in ["first_filter", "presets", "favourite_subscription", "back_to_handle_site"]


async def handle_site(subscription_title, event, edit=None):
    message = ""
    user_id = event.original_update.user_id
    subscription_id = (await SubscriptionDao.find_one_or_none(name=subscription_title)).id
    is_favourite = (
        await UserSubscriptionDao.find_one_or_none(user_id=event.chat_id, subscription_id=subscription_id)
    ).is_favourite
    favourite = "Удалить из избранного" if is_favourite else "Добавить в избранное"
    buttons = [
        [Button.inline("🔍 Запустить парсинг", data=json.dumps({"action": f"first_filter {subscription_title}"}))],
        [Button.inline("💾 Пресеты", data=json.dumps({"action": f"presets {subscription_title}"}))],
        [Button.inline(favourite, data=json.dumps({"action": f"favourite_subscription {subscription_title}"}))],
        [Button.inline("Назад", data=json.dumps({"action": "begin_parsing"}))],
    ]

    if "DEPOP" in subscription_title:
        title = flag(subscription_title.split(".")[1]) + " " + subscription_title
        subscription_id = (await SubscriptionDao.find_one_or_none(name=subscription_title)).id
        expired_at = (
            await UserSubscriptionDao.find_one_or_none(user_id=user_id, subscription_id=subscription_id)).expired_at
        time = moscow_time(expired_at)
        message = f"Площадка: [{title}]({depop_url})\nПодписка закончится (год-месяц-число): {time} по МСК"

    elif "GRAILED":
        pass

    if edit:
        await client_bot.edit_message(event.chat_id, event.original_update.msg_id, buttons=buttons)
    else:
        await client_bot.send_file(event.chat_id, caption=message, file=media,
                                   buttons=buttons)


@client_bot.on(events.CallbackQuery(func=parsing_site_callback_filter))
async def parsing_site_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    name = action.split(" ")[1]
    subscription_id = (await SubscriptionDao.find_one_or_none(name=name)).id
    if "first_filter" in action:
        await first_filter(event.chat_id, subscription_id)
    elif "presets" in action:
        await presets(event.chat_id, subscription_id)
    elif "favourite_subscription" in action:
        await add_to_favourite(event.chat_id, subscription_id)
        await handle_site(name, event, edit=True)
    elif "back_to_handle_site":
        await handle_site(name, event)


async def first_filter(chat_id, subscription_id):
    buttons = [[Button.inline("Назад", data=json.dumps({"action": "begin_parsing"}))]]
    message = "💡 Введите ссылки на категории или ключевые слова через запятую [Max: 10]" \
              "\n\nПример ссылки: https://www.depop.com/search/?q=vintage,\n" \
              "https://www.depop.com/search/?q=nike+air+force&priceMin=1&priceMax=123123"

    filter_id = (await FilterDao.add(value="Ссылки : ", question_number=1)).id
    user_id = chat_id
    await UserFilterSubscriptionDao.add(user_id=user_id, filter_id=filter_id, subscription_id=subscription_id)
    await client_bot.send_file(chat_id, caption=message, file=media,
                               buttons=buttons)


async def second_filter(user_id, subscription_id, filter_id):
    message = "💰 Введите диапазон цены товара:\nПример: 100-80000"
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    value = filter_entity.value + "Цена : "
    await FilterDao.update(filter_id, value=value)
    button = [[Button.text("Не использовать фильтр", resize=True, single_use=True)]]
    await client_bot.send_message(user_id, message=message, buttons=button)


async def third_filter(user_id, subscription_id, filter_id):
    message = "🔽 Введите минимальное кол-во проданных товаров продавца"
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    value = filter_entity.value + "Кол-во проданных товаров продавца : "
    await FilterDao.update(filter_id, value=value)
    button = [[Button.text("Не использовать фильтр", resize=True, single_use=True)]]
    await client_bot.send_message(user_id, message=message, buttons=button)


async def fourth_filter(user_id, subscription_id, filter_id):
    message = "🗓 Укажите минимальный рейтинг продавца (1-5)\nПример: 4"
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    value = filter_entity.value + "Рейтинг продавца : "
    await FilterDao.update(filter_id, value=value)
    button = [[Button.text("Не использовать фильтр", resize=True, single_use=True)]]
    await client_bot.send_message(user_id, message=message, buttons=button)


async def fifth_filter(user_id, subscription_id, filter_id):
    message = "🗓 Укажите дату создания объявления\nПример: (год-месяц-число) 2015-12-24"
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    value = filter_entity.value + "Дата создания объявления : "
    await FilterDao.update(filter_id, value=value)
    button = [[Button.text("Не использовать фильтр", resize=True, single_use=True)]]
    await client_bot.send_message(user_id, message=message, buttons=button)


async def preset_choose(user_id):
    message = "💾 Вы хотите сохранить текущие настройки парсера?"
    button = [
        [
            Button.text("Да", resize=True, single_use=True),
            Button.text("Нет", resize=True, single_use=True)
        ]
    ]
    await client_bot.send_message(user_id, message=message, buttons=button)


async def preset_answer_handle(msg, user_id, subscription_id, filter_id):
    if msg.lower() == "да":
        message = "Введите название для пресета"
        await UserDao.update(user_id, bot_message=message)
        await client_bot.send_message(user_id, message=message)
    else:
        await run_parsing(user_id, subscription_id, filter_id)


async def add_to_favourite(user_id, subscription_id):
    user_subscription = await UserSubscriptionDao.find_one_or_none(user_id=user_id, subscription_id=subscription_id)
    is_favourite = user_subscription.is_favourite
    await UserSubscriptionDao.update(user_subscription.id, is_favourite=not is_favourite)
