import json

from telethon import Button, events
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.database.dao.PromocodeDao import PromocodeDao
from src.database.dao.UserDao import UserDao
from src.main import client_bot
from src.utils.utils import generate_random_string


def settings_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["settings_promocode"]


async def handle_admin_settings(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    buttons = [
        [
            Button.inline("➕ Промокод", data=json.dumps({"action": "settings_promocode"})),
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "admin"}))
        ]
    ]
    await client_bot.send_message(user_id, message="⚙ Настройки", buttons=buttons)


@client_bot.on(events.CallbackQuery(func=settings_callback_filter))
async def settings_callback_handler(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "settings_promocode":
        buttons = [
            [
                Button.inline("Назад", data=json.dumps({"action": "admin_settings"})),
            ]
        ]
        await client_bot.send_message(user_id, message="Введите сумму промокода", buttons=buttons)
        await UserDao.update(user_id, bot_message=f"Введите сумму промокода")


async def handle_activation_quantity(event, activation_sum):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    buttons = [
        [
            Button.inline("Назад", data=json.dumps({"action": "admin_settings"})),
        ]
    ]

    await client_bot.send_message(user_id, message="Введите кол-во активаций", buttons=buttons)
    await UserDao.update(user_id, bot_message=f"Введите кол-во активаций _{activation_sum}")


async def handle_promocode(event, sum, activation_quantity):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    buttons = [
        [
            Button.inline("Назад", data=json.dumps({"action": "admin_settings"})),
        ]
    ]

    while True:
        title = generate_random_string(6)
        exists = await PromocodeDao.find_one_or_none(title=title)
        if not exists:
            await PromocodeDao.add(title=title, sum=sum, activation_quantity=activation_quantity)
            await client_bot.send_message(user_id, message=f"Промокод **{title}** успешно добавлен", buttons=buttons)
            break
