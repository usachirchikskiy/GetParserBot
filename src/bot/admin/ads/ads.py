import asyncio
import json
from datetime import datetime

import pytz
import telethon
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from telethon import events, Button
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage, Message, MessageMediaDocument, \
    MessageMediaPhoto, InputDocument, InputPhoto

from src.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
from src.database.dao.MailingDao import MailingDao
from src.database.dao.UserDao import UserDao
from src.database.model.User import Mailing
from src.main import client_bot
from src.utils.utils import convert_from_moscow_to_utc, moscow_time

jobs = []
semaphore = asyncio.Semaphore(30)
jobstores = {
    'default': SQLAlchemyJobStore(url=f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
scheduler.start()


def ads_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["ads_mailing", "preview_delete"]


def mailing_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        if "confirm_mailing_" in action or "preview_mailing_" in action or "cancel_mailing_" in action:
            return True


async def handle_ads(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    buttons = [
        [
            Button.inline("📥 Рассылка", data=json.dumps({"action": "ads_mailing"})),
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "admin_ads"})),
        ]]
    await client_bot.send_message(user_id, message="💰 Реклама", buttons=buttons)


@client_bot.on(events.CallbackQuery(func=ads_callback_filter))
async def ads_callback_handler(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "ads_mailing":
        buttons = [[
            Button.inline("Назад", data=json.dumps({"action": "admin_ads"})),
        ]]
        await UserDao.update(user_id, bot_message=f"Введите текст рассылки")
        await client_bot.send_message(user_id, message="Введите текст рассылки", buttons=buttons)
    elif action == "preview_delete":
        await event.delete()


async def handle_time_of_mailings(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    message: Message = event.message
    media = message.media

    id = message.id
    type = "Message"
    access_hash = None

    if isinstance(media, MessageMediaDocument):
        id = media.document.id
        access_hash = media.document.access_hash
        type = "Document"
    elif isinstance(media, MessageMediaPhoto):
        id = media.photo.id
        access_hash = media.photo.access_hash
        type = "Photo"

    if message.entities is not None:
        entities = [entity.to_dict() for entity in message.entities]
    else:
        entities = []
    msg = message.message

    mailing = await MailingDao.find_one_or_none(id=id)
    if mailing is None: await MailingDao.add(id=id, access_hash=access_hash, type=type, message=msg, entities=entities)

    await UserDao.update(user_id, bot_message=f"Введите время рассылки по мск_{id}")
    buttons = [[
        Button.inline("Назад", data=json.dumps({"action": "admin_ads"})),
    ]]
    await client_bot.send_message(user_id, message="Введите время рассылки по мск (20:00 или 2021-10-10 20:00)",
                                  buttons=buttons)


async def handle_confirm_mail(event, mailing_id, time_input, utc_time):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    utc_time_naive = utc_time.replace(tzinfo=None)
    await MailingDao.update(mailing_id, send_at=utc_time_naive)
    buttons = [[
        Button.inline("✅ Подтвердить рассылку", data=json.dumps({"action": f"confirm_mailing_{mailing_id}"}))
    ],
        [
            Button.inline("👁 Предпросмотр", data=json.dumps({"action": f"preview_mailing_{mailing_id}"})),
            Button.inline("❌ Отменить рассылку", data=json.dumps({"action": f"cancel_mailing_{mailing_id}"})),
        ]]
    await client_bot.send_message(user_id, message=f"🕘 Время рассылки по мск: {time_input}",
                                  buttons=buttons)


async def mailings_start(mailing_id: int):
    message: Mailing = await MailingDao.find_one_or_none(id=mailing_id)
    type = message.type
    document = None

    if type == "Document":
        document = InputDocument(id=message.id, access_hash=message.access_hash, file_reference=b'')
    elif type == "Photo":
        document = InputPhoto(id=message.id, access_hash=message.access_hash, file_reference=b'')

    entities = [getattr(telethon.types, entity["_"])(**{k: v for k, v in entity.items() if k != "_"}) for entity in
                message.entities]

    users = await UserDao.find_all()
    await asyncio.gather(*(send_mailing_message(user.id, document, message.message, entities) for user in users))


async def send_preview_message(user_id, document, message, entities):
    buttons = [[
        Button.inline("❌ Понятно", data=json.dumps({"action": f"preview_delete"}))
    ]]
    if document:
        await client_bot.send_file(user_id, document, caption=message, formatting_entities=entities, buttons=buttons)
    else:
        await client_bot.send_message(user_id, message=message, formatting_entities=entities, buttons=buttons)


async def send_mailing_message(user_id, document, message, entities):
    async with semaphore:
        if document:
            await client_bot.send_file(user_id, document, caption=message, formatting_entities=entities)
        else:
            await client_bot.send_message(user_id, message=message, formatting_entities=entities)

        await asyncio.sleep(1 / 30)


@client_bot.on(events.CallbackQuery(func=mailing_callback_filter))
async def mailing_callback_handler(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    data = json.loads(event.data.decode("utf-8"))
    action = data['action']

    if "confirm_mailing_" in action:
        mailing_id = int(action.split("_")[-1])
        mailing: Mailing = await MailingDao.find_one_or_none(id=mailing_id)
        timezone = pytz.timezone("UTC")
        dt_with_timezone = timezone.localize(mailing.send_at)
        scheduler.add_job(mailings_start, 'date', run_date=dt_with_timezone, args=[mailing_id],
                          id=f'{mailing_id}_{dt_with_timezone}', replace_existing=True)
        msc_time = moscow_time(dt_with_timezone, '%Y-%m-%d %H:%M:%S%z')
        buttons = [[
            Button.inline("Назад", data=json.dumps({"action": "admin_ads"})),
        ]]
        await client_bot.edit_message(event.chat_id, event.original_update.msg_id,
                                      f"✅ Рассылка успешно создана. Время рассылки: {msc_time} по МСК", buttons=buttons)

    elif "preview_mailing_" in action:
        mailing_id = int(action.split("_")[-1])
        mailing_message = await get_mailing_message(mailing_id)
        await send_preview_message(user_id, mailing_message[0], mailing_message[1], mailing_message[2])

    elif "cancel_mailing_" in action:
        await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "✅ Рассылка успешно удалена")


async def get_mailing_message(mailing_id):
    message: Mailing = await MailingDao.find_one_or_none(id=mailing_id)
    type = message.type
    document = None

    if type == "Document":
        document = InputDocument(id=message.id, access_hash=message.access_hash, file_reference=b'')
    elif type == "Photo":
        document = InputPhoto(id=message.id, access_hash=message.access_hash, file_reference=b'')

    entities = [getattr(telethon.types, entity["_"])(**{k: v for k, v in entity.items() if k != "_"}) for entity in
                message.entities]

    return document, message.message, entities
