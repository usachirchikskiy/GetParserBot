import json

from telethon import Button, events
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.bot.admin.ads.ads import handle_ads
from src.bot.admin.settings.settings import handle_admin_settings
from src.bot.admin.users.users import handle_users
from src.main import client_bot


def admin_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["admin_users", "admin_ads", "admin_settings"]


async def handle_admin(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    buttons = [
            [
                Button.inline("👤 Пользователи", data=json.dumps({"action": "admin_users"})),
                    Button.inline("💰 Реклама", data=json.dumps({"action": "admin_ads"}))
            ],
        [
            Button.inline("Настройки", data=json.dumps({"action": "admin_settings"}))
        ]
    ]

    await client_bot.send_message(user_id, message="Вы перешли в панели администратора", buttons=buttons)


@client_bot.on(events.CallbackQuery(func=admin_callback_filter))
async def menu_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "admin_users":
        await handle_users(event)
    elif action == "admin_ads":
        await handle_ads(event)
    elif action == "admin_settings":
        await handle_admin_settings(event)
