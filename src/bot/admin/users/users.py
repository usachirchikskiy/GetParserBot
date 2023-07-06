import json
from datetime import datetime, timedelta

import pytz
from sqlalchemy import and_, extract
from telethon import Button, events
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage, User

from src.database.dao.UserDao import UserDao
from src.main import client_bot


def users_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["users_search", "user_top_balance"]


def user_change_block_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        if "users_change_balance_" in action or "users_block_" in action:
            return True


async def handle_users(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    all_users = await UserDao.count_filtered()

    todays_users = await UserDao.count_filtered(UserDao.model.created_at >= datetime.now(pytz.timezone('UTC')).date())

    yesterday = datetime.now(pytz.timezone('UTC')).date() - timedelta(days=1)
    yesterdays_users = await UserDao.count_filtered(
        and_(UserDao.model.created_at >= yesterday,
             UserDao.model.created_at < datetime.now(pytz.timezone('UTC')).date()))

    current_month_users = await UserDao.count_filtered(
        extract('month', UserDao.model.created_at) == datetime.now(pytz.timezone('UTC')).month)

    last_month = datetime.now(pytz.timezone('UTC')).month - 1 if datetime.now(pytz.timezone('UTC')).month != 1 else 12
    last_month_users = await UserDao.count_filtered(extract('month', UserDao.model.created_at) == last_month)

    message = f'''
👤 Всего пользователей: {all_users}
👤 Сегодня: {todays_users}
👤 Вчера: {yesterdays_users}
👤 Месяц: {current_month_users}
👤 Пред.месяц: {last_month_users}
'''

    buttons = [
        [
            Button.inline("👤 Поиск пользователя", data=json.dumps({"action": "users_search"})),
        ],
        [
            Button.inline("Топ пользователей по балансу", data=json.dumps({"action": "user_top_balance"})),
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "admin"}))
        ]
    ]
    await client_bot.send_message(user_id, message=message, buttons=buttons)


@client_bot.on(events.CallbackQuery(func=users_callback_filter))
async def users_callback_handler(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "users_search":
        buttons = [
            [
                Button.inline("Назад", data=json.dumps({"action": "admin_users"})),
            ]
        ]
        await client_bot.send_message(user_id, message="Введите USERNAME или ID пользователя", buttons=buttons)
        await UserDao.update(user_id, bot_message="Введите USERNAME или ID пользователя")

    elif action == "user_top_balance":
        await handle_user_top_balance(event)


async def handle_users_search(event, search_query):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    if search_query.isdigit():
        search_query = int(search_query)
    user_found = await client_bot.get_entity(search_query)

    if isinstance(user_found, User):
        user = await UserDao.find_one_or_none(id=user_found.id)
        if user:
            id = f"ID: {user_found.id}"
            username = f"USERNAME: @{user_found.username}"
            balance = f"БАЛАНС: {user.balance}"
            message = f"{id}\n{username}\n{balance}\n"

            buttons = [
                [
                    Button.inline("Заблокировать", data=json.dumps({"action": f"users_block_{user_found.id}"})),
                ],
                [
                    Button.inline("Изменить баланс",
                                  data=json.dumps({"action": f"users_change_balance_{user_found.id}"})),
                ],
                [
                    Button.inline("Назад", data=json.dumps({"action": "users_search"})),
                ]
            ]
            await client_bot.send_message(user_id, message=message, buttons=buttons)


async def handle_user_top_balance(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    users = await UserDao.top_balance_users()
    buttons = [[
        Button.inline("Назад", data=json.dumps({"action": "admin_users"})),
    ]]
    message = "\n".join(f"{index + 1}) ID: {user.id}\nБАЛАНС: {user.balance}\n" for index, user in enumerate(users))
    await client_bot.send_message(user_id, message=message, buttons=buttons)


@client_bot.on(events.CallbackQuery(func=user_change_block_callback_filter))
async def user_change_block_callback_handler(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if "users_change_balance_" in action:
        id = action.split("_")[-1]
        buttons = [
            [
                Button.inline("Назад", data=json.dumps({"action": "users_search"})),
            ]
        ]
        await client_bot.send_message(user_id, message="Введите новый баланс пользователя", buttons=buttons)
        await UserDao.update(user_id, bot_message=f"Введите новый баланс пользователя {id}")

    elif "users_block_" in action:
        id = action.split("_")[-1]
        await handle_user_block(event, int(id))


async def handle_user_change_balance(event, changed_balance, user_id_changed):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    await UserDao.update(id=user_id_changed, balance=changed_balance)

    buttons = [[
        Button.inline("Назад", data=json.dumps({"action": "admin_users"})),
    ]]
    message = f"Баланс пользователя {user_id_changed} успешно изменен"
    await client_bot.send_message(user_id, message=message, buttons=buttons)


async def handle_user_block(event, id):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    await UserDao.update(id=id, blocked=True)

    buttons = [[
        Button.inline("Назад", data=json.dumps({"action": "admin_users"})),
    ]]
    message = f"Пользователь {id} заблокирован"
    await client_bot.send_message(user_id, message=message, buttons=buttons)
