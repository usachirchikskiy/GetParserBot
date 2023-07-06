import json

from aiocryptopay.const import InvoiceStatus
from telethon import Button, events
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.database.dao.Associations import UserPaymentSystemDao
from src.database.dao.PaymentSystemDao import PaymentSystemDao
from src.main import client_bot, crypto_pay
from src.database.dao.UserDao import UserDao
from src.utils.constants import percentage_number
from src.utils.validation import Validation


def crypto_bot_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["bitcoin_btc", "ton", "teather_usdt", "check_payment", "cancel_payment", "back_to_crypto_bot"]


async def handle_crypto_bot(event):
    buttons = [
        [
            Button.inline("Bitcoin BTC", data=json.dumps({"action": "bitcoin_btc"})),
            Button.inline("TON", data=json.dumps({"action": "ton"}))
        ],
        [
            Button.inline("Teather USDT", data=json.dumps({"action": "teather_usdt"}))
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_top_up"})),
        ],
    ]

    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    payment_system_id = (await PaymentSystemDao.find_one_or_none(title=None)).id
    await UserPaymentSystemDao.add_or_update(user_id=user_id, payment_system_id=payment_system_id, type="")
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите криптовалюту", buttons=buttons)


@client_bot.on(events.CallbackQuery(func=crypto_bot_callback_filter))
async def crypto_bot_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "bitcoin_btc":
        await handle_crypto_type(event, 'BTC')
    elif action == "ton":
        await handle_crypto_type(event, 'TON')
    elif action == "teather_usdt":
        await handle_crypto_type(event, 'USDT')

    elif action == "check_payment":
        await handle_check_payment(event, data['id'], data['amount'])
    elif action == "cancel_payment":
        await handle_cancel_payment(event)

    elif action == "back_to_crypto_bot":
        await handle_crypto_bot(event)


async def handle_crypto_type(event, type):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    payment_system_id = (await PaymentSystemDao.find_one_or_none(title="Cryptobot")).id
    await UserPaymentSystemDao.add_or_update(user_id=user_id, payment_system_id=payment_system_id, type=type)
    buttons = [
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_crypto_bot"})),
        ],
    ]
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Введите сумму пополнения в RUB",
                                  buttons=buttons)


async def check_input_crypto_bot(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    msg = event.raw_text
    if Validation.validate_positive_float(msg):
        await payment_generated(event, float(msg))
    else:
        await client_bot.send_message(user_id, message=Validation.incorrect_input_balance)


async def payment_generated(event, amount_to_pay):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    crypto_type = (await UserPaymentSystemDao.find_one_or_none(user_id=user_id)).type
    payment_system_id = (await PaymentSystemDao.find_one_or_none(title=None)).id
    await UserPaymentSystemDao.add_or_update(user_id=user_id, payment_system_id=payment_system_id, type="")
    result = 1  # TODO() await coin_market.get_in_crypto(user.type, amount_to_pay)
    invoice = await crypto_pay.create_invoice(crypto_type, result)
    buttons = [
        [
            Button.url("✅ Оплатить", url=invoice.pay_url)
        ],
        [
            Button.inline("♻ Проверить оплату",
                          data=json.dumps({"action": "check_payment",
                                           "id": invoice.invoice_id,
                                           "amount": result
                                           }))
        ],
        [
            Button.inline("❌ Отменить", data=json.dumps({"action": "cancel_payment"}))
        ]
    ]
    text = '✅ Счёт сгенерирован\n\n❓Для оплаты перейдите по ссылке'
    await client_bot.send_message(event.chat_id, text, buttons=buttons)


async def handle_check_payment(event, invoice_id, amount_to_pay):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    result = await crypto_pay.get_invoice(invoice_id)
    if result.status == InvoiceStatus.ACTIVE:
        text = "❗ Счёт всё ещё не оплачен"
        await client_bot.send_message(user_id, text)
    elif result.status == InvoiceStatus.PAID:
        user = await UserDao.find_one_or_none(id=user_id)
        balance = user.balance + amount_to_pay

        await UserDao.update(user_id, balance=balance)
        text = f"✅ Счёт успешно оплачен. Ваш баланс пополнен на {amount_to_pay} RUB"
        buttons = [[
            Button.inline("Назад в меню", data=json.dumps({"action": "back_to_main_menu"}))
        ]]
        await client_bot.edit_message(user_id, event.original_update.msg_id, text, buttons=buttons)

        if user.referrer_id:
            user_referrer = await UserDao.find_one_or_none(id=user.referrer_id)
            if user_referrer:
                referal_earned = round(amount_to_pay * percentage_number, 2)
                earned = user_referrer.earned + referal_earned
                balance = user_referrer.balance + referal_earned
                await UserDao.update(id=user.referrer_id, balance=balance, earned=earned)
                await client_bot.send_message(entity=user.referrer_id,
                                              message=f"✅ Ваш баланс пополнен на {referal_earned} RUB (Реферальная система)")


async def handle_cancel_payment(event):
    buttons = [
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_crypto_bot"})),
        ],
    ]
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "❌ Оплата отменена", buttons=buttons)
