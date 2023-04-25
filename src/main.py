import json

from aiocryptopay.const import InvoiceStatus
from telethon import TelegramClient, events, Button
import logging

from telethon.tl.types import PeerUser

from src.coin_market.CoinMarket import CoinMarket
from src.config import STATIC
from src.crypto_pay.CryptoPay import CryptoPay
from src.dao.UserDao import UserDao
from src.utils.utils import convert_to_float

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

client_bot = TelegramClient("bot", 16819926, "65788ccadd6ccbd8695f19710b41a2fd").start(
    bot_token="6059203083:AAEV8bjjzu32G0ZcKd8ggAo_lqN6-HqwiRc")

client_user = TelegramClient("bitpapa", api_id=16819926, api_hash="65788ccadd6ccbd8695f19710b41a2fd").start()

crypto_pay = CryptoPay.get_instance()
coin_market = CoinMarket.get_instance()


@client_user.on(events.NewMessage())
async def new_message(event):
    sender = await event.get_sender()
    await client_user.send_message(sender,"Hello")

# Buttons
async def main_menu(event, from_callback):
    try:
        id = event.original_update.message.peer_id.user_id
    except Exception as e:
        id = event.original_update.user_id

    user = await UserDao.find_one_or_none(id=id)
    media = STATIC + "get_parser.jpg"
    buttons = [
        [
            Button.inline("Начать парсинг", data=json.dumps({"action": "begin_parsing"})),
            Button.inline("Пополнить баланс", data=json.dumps({"action": "top_up"}))
        ],
        [
            Button.inline("Профиль", data=json.dumps({"action": "profile"})),
            Button.inline("Тех поддержка", data=json.dumps({"action": "tech_support"}))
        ],
        [
            Button.inline("Реферальная система", data=json.dumps({"action": "referral_system"})),
            Button.inline("Настройки", data=json.dumps({"action": "settings"}))
        ],
    ]
    if not from_callback:
        await client_bot.send_file(event.chat_id, caption="Ваш баланс {}".format(user.balance), file=media,
                                   buttons=buttons)
    else:
        await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Ваш баланс {}".format(user.balance),
                                      file=media, buttons=buttons)


@client_bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "begin_parsing":
        await handle_begin_parsing(event)
    elif action == "top_up":
        await handle_top_up(event)
    elif action == "profile":
        await handle_profile(event)
    elif action == "tech_support":
        await handle_technical_support(event)
    elif action == "referral_system":
        await handle_referral_system(event)
    elif action == "settings":
        await handle_settings(event)

    ##Пополнить баланс
    elif action == "crypto_bot":
        await handle_crypto_bot(event)
    elif action == "total_coin":
        await handle_total_coin(event)
    elif action == "bit_papa":
        await handle_bit_papa(event)
    elif action == "yoo_money":
        await handle_yoo_money(event)
    elif action == "back_to_main_menu":
        await main_menu(event, True)

    ##CryptoBot
    elif action == "bitcoin_btc":
        await handle_crypto_type(event, 'BTC')
    elif action == "ton":
        await handle_crypto_type(event, 'TON')
    elif action == "teather_usdt":
        await handle_crypto_type(event, 'USDT')
    elif action == "back_to_top_up":
        await handle_top_up(event)
    ##
    elif action == "check_payment":
        await handle_check_payment(event, data['id'], data['amount'])
    elif action == "cancel_payment":
        await handle_cancel_payment(event)
    elif action == "back_to_crypto_bot":
        await handle_crypto_bot(event)


async def handle_begin_parsing(event):
    # Your code for handling parsing goes here
    pass


async def handle_top_up(event):
    # Your code for handling top-up goes here
    buttons = [
        [
            Button.inline("CryptoBot", data=json.dumps({"action": "crypto_bot"})),
            Button.inline("TotalCoin", data=json.dumps({"action": "total_coin"}))
        ],
        [
            Button.inline("Bitpapa", data=json.dumps({"action": "bit_papa"})),
            Button.inline("YooMoney", data=json.dumps({"action": "yoo_money"}))
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_main_menu"})),
        ],
    ]

    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите способ пополнения",
                                  buttons=buttons)


async def handle_profile(event):
    # Your code for handling profile goes here
    pass


async def handle_technical_support(event):
    # Your code for handling technical support goes here
    pass


async def handle_referral_system(event):
    # Your code for handling the referral system goes here
    pass


async def handle_settings(event):
    # Your code for handling settings goes here
    pass


##################### Пополнить баланс #####################
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
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите криптовалюту", buttons=buttons)


async def handle_total_coin(event):
    pass


async def handle_bit_papa(event):
    pass


async def handle_yoo_money(event):
    pass


##################### CryptoBot #####################
async def handle_crypto_type(event, type):
    id = event.original_update.user_id
    buttons = [
        [
            Button.inline("Назад", data=json.dumps({"action": "back_to_crypto_bot"})),
        ],
    ]
    await UserDao.update(id, checking_status='CHECK INPUT CRYPTOBOT', type=type)
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Введите сумму пополнения в RUB",
                                  buttons=buttons)


async def payment_generated(event, amount_to_pay):
    id = event.original_update.message.peer_id.user_id
    user = await UserDao.update(id, checking_status="")
    result = 1  # TODO await coin_market.get_in_crypto(user.type, amount_to_pay)
    invoice = await crypto_pay.create_invoice(user.type, result)
    buttons = [
        [
            Button.url("✅ Оплатить", url=invoice.pay_url)
        ],
        [
            Button.inline("♻️ Проверить оплату",
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


async def handle_check_payment(event, payment_id, amount_to_pay):
    id = event.original_update.user_id
    result = await crypto_pay.get_invoice(payment_id)
    if result.status == InvoiceStatus.ACTIVE:
        text = "❗️ Счёт всё ещё не оплачен"
    elif result.status == InvoiceStatus.PAID:
        await UserDao.update(id, balance=amount_to_pay)
        text = "✅ Счёт успешно оплачен"
    await client_bot.send_message(event.chat_id, text)


async def handle_cancel_payment(event):
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "❌ Оплата отменена")


##INPUT_ERROR
async def handle_input_error(event):
    buttons = [
        [
            Button.inline("Назад", "Назад в меню"),
        ],
    ]
    await event.respond("**Введите число ❗️**", buttons=buttons)


@client_bot.on(events.NewMessage(pattern=r'^(?!/start).*$'))
async def number_handler(event):
    id = event.original_update.message.peer_id.user_id
    user = await UserDao.find_one_or_none(id=id)
    if user is not None:
        if user.checking_status == "CHECK INPUT CRYPTOBOT":
            msg = event.raw_text
            if convert_to_float(msg):
                await payment_generated(event, float(msg))
            else:
                await handle_input_error(event)


@client_bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    id = event.original_update.message.peer_id.user_id
    user = await UserDao.find_one_or_none(id=id)
    if user is None:
        await UserDao.add(id=id, type="", checking_status="", balance=0.0)
    await main_menu(event, False)


if __name__ == "__main__":
    client_bot.run_until_disconnected()
    client_user.run_until_disconnected()

