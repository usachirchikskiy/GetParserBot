import json

from telethon import Button, events

from src.bot.top_up.bit_papa import handle_bit_papa
from src.bot.top_up.crypto_bot import handle_crypto_bot
from src.database.dao.Associations import UserPaymentSystemDao
from src.database.dao.PaymentSystemDao import PaymentSystemDao
from src.main import client_bot


def top_up_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["crypto_bot", "bit_papa", "payok", "back_to_top_up"]


async def handle_top_up(event):
    buttons = [
        [
            Button.inline("CryptoBot", data=json.dumps({"action": "crypto_bot"})),
            # Button.inline("TotalCoin", data=json.dumps({"action": "total_coin"}))
        ],
        [
            Button.inline("Bitpapa", data=json.dumps({"action": "bit_papa"})),
            # Button.inline("YooMoney", data=json.dumps({"action": "yoo_money"}))
        ],
        [
            Button.inline("Payok", data=json.dumps({"action": "payok"}))
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_main_menu"})),
        ],
    ]

    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите способ пополнения",
                                  buttons=buttons)


@client_bot.on(events.CallbackQuery(func=top_up_callback_filter))
async def top_up_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "crypto_bot":
        await handle_crypto_bot(event)
    elif action == "bit_papa":
        await handle_bit_papa(event)
    elif action == "payok":
        pass
    elif action == "back_to_top_up":
        user_id = event.original_update.user_id
        payment_system_id = (await PaymentSystemDao.find_one_or_none(title="Nothing")).id
        await UserPaymentSystemDao.add_or_update(user_id=user_id, payment_system_id=payment_system_id, type="")
        await handle_top_up(event)
