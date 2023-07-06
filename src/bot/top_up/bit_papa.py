import asyncio
import json
import logging
import re

from telethon import Button
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.database.dao.Associations import UserPaymentSystemDao
from src.database.dao.PaymentSystemDao import PaymentSystemDao
from src.database.dao.UserDao import UserDao
from src.main import client_bot, client_user_bitpapa
from src.utils.constants import percentage_number
from src.utils.utils import btc_to_rub


async def handle_bit_papa(event):
    buttons = [
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_top_up"})),
        ],
    ]
    msg = "📤 Отправьте чек Bitpapa в этот чат\n\n❓ Курс должен быть Binance, валюта RUB"

    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    payment_system_id = (await PaymentSystemDao.find_one_or_none(title="Bitpapa")).id
    await UserPaymentSystemDao.add_or_update(user_id=user_id, payment_system_id=payment_system_id, type="")
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, msg, buttons=buttons)


async def check_input_bit_papa(event):
    msg = event.raw_text
    result = await handle_bit_papa_cheque(msg)
    if result == -1:
        await event.respond("❗ Невалидный чек")
    else:
        if isinstance(event.original_update, UpdateBotCallbackQuery):
            user_id = event.original_update.user_id
        elif isinstance(event.original_update, UpdateNewMessage):
            user_id = event.original_update.message.peer_id.user_id

        user = await UserDao.find_one_or_none(id=user_id)
        balance = user.balance + result

        await UserDao.update(user_id, balance=balance)
        text = f"✅ Ваш баланс пополнен на {result} RUB"
        buttons = [[
            Button.inline("Назад в меню", data=json.dumps({"action": "back_to_main_menu"}))
        ]]
        payment_system_id = (await PaymentSystemDao.find_one_or_none(title=None)).id
        await UserPaymentSystemDao.add_or_update(user_id=user_id, payment_system_id=payment_system_id, type="")
        await event.respond(text, buttons=buttons)

        if user.referrer_id:
            user_referrer = await UserDao.find_one_or_none(id=user.referrer_id)
            if user_referrer:
                referal_earned = round(result * percentage_number, 2)
                earned = user_referrer.earned + referal_earned
                balance = user_referrer.balance + referal_earned
                await UserDao.update(id=user.referrer_id, balance=balance, earned=earned)
                await client_bot.send_message(entity=user.referrer_id,
                                              message=f"✅ Ваш баланс пополнен на {referal_earned} RUB (Реферальная система)")


async def handle_bit_papa_cheque(msg):
    cheque_id = re.findall(
        r"https://t\.me/bitpapa_bot\?start=(papa_code_[A-Z0-9]+)", msg
    )
    if len(cheque_id) < 1:
        return -1

    await client_user_bitpapa.send_message("bitpapa_bot", f"/start {cheque_id[0]}")

    while True:
        message = (await client_user_bitpapa.get_messages("bitpapa_bot", limit=1))[0]
        await asyncio.sleep(1)
        if "Этот код кто-то уже активировал" in message.message:
            return -1
        elif "Код на сумму" in message.message:
            try:
                response = float(
                    re.findall(r"Код на сумму (\d+\.\d+) BTC успешно", message.message)[0]
                )
                return round(response * btc_to_rub(), 2)
            except Exception as e:
                logging.error(f'ERROR {e}')
                return -1
