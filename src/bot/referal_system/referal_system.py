import json

from telethon import Button
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.database.dao.UserDao import UserDao
from src.database.model.User import User
from src.main import client_bot
from src.utils.constants import media, percentage_string


async def handle_referral_system(event):
    id = None

    if isinstance(event.original_update, UpdateBotCallbackQuery):
        id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        id = event.original_update.message.peer_id.user_id

    user_entity: User = await UserDao.find_one_or_none_user(id=id)
    earned = user_entity.earned
    referrals = len(user_entity.referrals)

    text = f'''
👥 Реферальная сеть\n
Ваша реферельная ссылка:\nhttps://t.me/silipublic_bot?start={id}\n
За все время вы заработали - {earned} RUB
Вы пригласили - {referrals} людей\n
Если человек приглашенный по вашей реферальной ссылки пополнит баланс, то вы получите {percentage_string} от суммы его депозита
    '''

    buttons = [[
        Button.inline("Назад", data=json.dumps({"action": "back_to_main_menu"})),
    ]]
    await client_bot.send_file(event.chat_id, caption=text, file=media,
                               buttons=buttons)
