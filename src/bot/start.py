import asyncio
import json
from datetime import datetime

import pytz
from telethon import Button, events
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.bot.admin.admin import handle_admin
from src.bot.admin.ads.ads import handle_time_of_mailings, handle_confirm_mail
from src.bot.admin.settings.settings import handle_activation_quantity, handle_promocode
from src.bot.admin.users.users import handle_users_search, handle_user_change_balance
from src.bot.parsing.parsing_menu import handle_begin_parsing
from src.bot.parsing.parsing_site import second_filter, third_filter, fifth_filter, \
    preset_answer_handle, fourth_filter, preset_choose, run_parsing, sixth_filter, seventh_filter
from src.bot.referal_system.referal_system import handle_referral_system
from src.bot.top_up.bit_papa import check_input_bit_papa
from src.bot.top_up.crypto_bot import check_input_crypto_bot
from src.bot.top_up.top_up_menu import handle_top_up
from src.database.dao.Associations import UserPaymentSystemDao, UserFilterSubscriptionDao
from src.database.dao.FilterDao import FilterDao
from src.database.dao.PaymentSystemDao import PaymentSystemDao
from src.database.dao.PromocodeDao import PromocodeDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.database.dao.UserDao import UserDao
from src.main import client_bot, client_user_bitpapa
from src.utils.constants import media, parsing_tasks, tech_support_link, admin_id
from src.utils.utils import convert_from_moscow_to_utc
from src.utils.validation import Validation


def menu_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["begin_parsing", "top_up", "referral_system", "settings", "admin", "back_to_main_menu"]


async def menu(event, from_callback):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    user = await UserDao.find_one_or_none(id=user_id)

    buttons = [
        [
            Button.inline("Начать парсинг", data=json.dumps({"action": "begin_parsing"})),
            Button.inline("Пополнить баланс", data=json.dumps({"action": "top_up"}))
        ],
        [
            Button.inline("Реферальная система", data=json.dumps({"action": "referral_system"})),
            Button.url('Тех поддержка', tech_support_link)
        ],
        # [
        # Button.inline("Профиль", data=json.dumps({"action": "profile"})),
        # Button.inline("Настройки", data=json.dumps({"action": "settings"}))
        # ],
    ]
    if user_id == admin_id:
        admin_button = [
            Button.inline("Войти в панель администратора", data=json.dumps({"action": "admin"})),
        ]
        buttons.append(admin_button)

    if not from_callback:
        await client_bot.send_file(user_id, caption="Ваш баланс {}".format(user.balance), file=media,
                                   buttons=buttons)
    else:
        await client_bot.edit_message(user_id, event.original_update.msg_id, "Ваш баланс {}".format(user.balance),
                                      file=media, buttons=buttons)


@client_bot.on(events.CallbackQuery(func=menu_callback_filter))
async def menu_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "begin_parsing":
        await handle_begin_parsing(event)
    elif action == "top_up":
        await handle_top_up(event)
    elif action == "referral_system":
        await handle_referral_system(event)
    elif action == "back_to_main_menu":
        await menu(event, True)
    elif action == "admin":
        await handle_admin(event)


### Handle Text and Start command
@client_bot.on(events.NewMessage(pattern=r'^/start \d+$'))
async def start_referral(event):
    referrer_id = float(event.raw_text.split(" ")[1])

    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    user_referal_entity = await UserDao.find_one_or_none(id=referrer_id)

    if user_referal_entity:
        user = await UserDao.find_one_or_none(id=user_id)
        if user is None:
            await UserDao.add(id=user_id, balance=0.0, referrer_id=referrer_id, earned=0.0)


@client_bot.on(events.NewMessage(pattern=r'^(?!/start).*'))
async def user_input_handler(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    user = await UserDao.find_one_or_none(id=user_id)
    blocked = user.blocked
    if not blocked:
        await handle_promocode_message(event)
        await handle_payment(event)
        await handle_message(event)


@client_bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    user = await UserDao.find_one_or_none(id=user_id)
    if user is None:
        await UserDao.add(id=user_id, balance=0.0, earned=0.0)
        await menu(event, False)
    else:
        blocked = user.blocked
        if not blocked:
            await menu(event, False)


async def handle_promocode_message(event):
    promocode: str = event.raw_text

    if len(promocode) == 6 and promocode.isalpha():
        if isinstance(event.original_update, UpdateBotCallbackQuery):
            user_id = event.original_update.user_id
        elif isinstance(event.original_update, UpdateNewMessage):
            user_id = event.original_update.message.peer_id.user_id

        promocode_entity = await PromocodeDao.find_one_or_none(title=promocode)
        if promocode_entity:
            used_quantity = promocode_entity.used_quantity
            activation_quantity = promocode_entity.activation_quantity

            if activation_quantity > used_quantity:
                used_quantity += 1
                promocode_sum = promocode_entity.sum
                await PromocodeDao.update(id=promocode_entity.id, used_quantity=used_quantity)

                user_entity = await UserDao.find_one_or_none(id=user_id)
                balance = user_entity.balance + promocode_sum
                await UserDao.update(id=user_id, balance=balance)
                await client_bot.send_message(user_id, message=f"На ваш баланс зачислено {promocode_sum} RUB")

            else:
                await PromocodeDao.delete(id=promocode_entity.id)
                await client_bot.send_message(user_id, message="Промокод недействителен")


async def handle_payment(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    user_payment_system = await UserPaymentSystemDao.find_one_or_none(user_id=user_id)
    if user_payment_system is not None:
        payment_system_id = user_payment_system.payment_system_id
        if payment_system_id == 1:
            await check_input_bit_papa(event)
        elif payment_system_id == 2:
            await check_input_crypto_bot(event)
        elif payment_system_id == 3:
            pass


async def handle_last_bot_message(event, bot_message, userFilterSubscription, msg):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    if bot_message == "Введите название для пресета":
        await UserFilterSubscriptionDao.update(userFilterSubscription.id, is_favourite=True, title=msg)
        await UserDao.update(user_id, bot_message=None)
        await run_parsing(user_id, userFilterSubscription.subscription_id, userFilterSubscription.filter_id)

    elif bot_message == "Введите USERNAME или ID пользователя":
        await UserDao.update(user_id, bot_message=None)
        await handle_users_search(event, msg)

    elif "Введите новый баланс пользователя" in bot_message:
        if Validation.validate_positive_float(msg):
            user_id_changed = int(bot_message.split(" ")[-1])
            await UserDao.update(user_id, bot_message=None)
            await handle_user_change_balance(event, float(msg), user_id_changed)
        else:
            await client_bot.send_message(user_id, message=Validation.incorrect_input_balance)

    elif "Введите сумму промокода" in bot_message:
        if Validation.validate_positive_float(msg):
            await UserDao.update(user_id, bot_message=None)
            await handle_activation_quantity(event, msg)
        else:
            await client_bot.send_message(user_id, message=Validation.incorrect_input_balance)

    elif "Введите кол-во активаций" in bot_message:
        if Validation.validate_positive_integer(msg):
            activation_quantity = int(msg)
            sum = float(bot_message.split("_")[-1])
            await UserDao.update(user_id, bot_message=None)
            await handle_promocode(event, sum, activation_quantity)
        else:
            await client_bot.send_message(user_id, message=Validation.incorrect_input_quantity)

    elif bot_message == "Введите текст рассылки":
        await UserDao.update(user_id, bot_message=None)
        await handle_time_of_mailings(event)

    elif "Введите время рассылки по мск" in bot_message:
        if Validation.validate_time_or_datetime(msg):
            utc_time = convert_from_moscow_to_utc(msg)
            current_datetime = datetime.now(pytz.utc)

            if current_datetime < utc_time:
                mailing_id = int(bot_message.split("_")[-1])
                await UserDao.update(user_id, bot_message=None)
                await handle_confirm_mail(event, mailing_id, msg, utc_time)
            else:
                await client_bot.send_message(user_id, message=Validation.incorrect_input)
        else:
            await client_bot.send_message(user_id, message=Validation.incorrect_input)


async def handle_message(event):
    if isinstance(event.original_update, UpdateBotCallbackQuery):
        user_id = event.original_update.user_id
    elif isinstance(event.original_update, UpdateNewMessage):
        user_id = event.original_update.message.peer_id.user_id

    userFilterSubscription = await UserFilterSubscriptionDao.get_last_added(user_id)
    msg = event.raw_text
    last_bot_message = (await UserDao.find_one_or_none(id=user_id))

    if last_bot_message.bot_message:
        await handle_last_bot_message(event, last_bot_message.bot_message, userFilterSubscription, msg)

    if msg == "Остановить парсер":
        if user_id in parsing_tasks and not parsing_tasks[user_id].done():
            parsing_tasks[user_id].cancel()
            del parsing_tasks[user_id]
            await client_bot.send_message(user_id, "Парсер остановлен")

    if userFilterSubscription:
        subscription_id = userFilterSubscription.subscription_id
        filter_id = userFilterSubscription.filter_id
        await handle_question_filters(user_id, msg, filter_id, subscription_id)


async def handle_question_filters(user_id, msg, filter_id, subscription_id):
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    question_number = filter_entity.question_number
    if question_number == 1:  # WORDS
        await handle_question_first(filter_entity, msg, question_number, user_id)
    elif question_number == 2:  # Price
        await handle_question_second(filter_entity, msg, question_number, user_id, subscription_id)
    elif question_number == 3:
        await handle_question_third(filter_entity, msg, question_number, user_id, subscription_id)
    elif question_number == 4:
        await handle_question_fourth(filter_entity, msg, question_number, user_id, subscription_id)
    elif question_number == 5:
        await handle_question_fifth(filter_entity, msg, question_number, user_id, subscription_id)
    elif question_number == 6:
        await handle_question_sixth(filter_entity, msg, question_number, user_id, subscription_id)
    elif question_number == 7:
        await handle_question_seventh(filter_entity, msg, question_number, user_id, subscription_id)
    elif question_number == 8:
        await handle_question_eighth(filter_entity, msg, question_number, user_id, subscription_id)


async def handle_question_first(filter_entity, msg, question_number, user_id):
    value = filter_entity.value + msg + "\n"
    question_number += 1
    await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
    await second_filter(user_id, filter_entity.id)


async def handle_question_second(filter_entity, msg, question_number, user_id, subscription_id):
    if Validation.validate_price_range(msg):
        value = filter_entity.value + msg + "\n"
        question_number += 1
        await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
        await third_filter(user_id, subscription_id, filter_entity.id)
    else:
        await client_bot.send_message(user_id, Validation.incorrect_input_price_range)


async def handle_question_third(filter_entity, msg, question_number, user_id, subscription_id):
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name  # TODO FOR FUTURE
    if Validation.validate_positive_integer(msg):
        value = filter_entity.value + msg + "\n"
        question_number += 1
        await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
        await fourth_filter(user_id, subscription_id, filter_entity.id)
    else:
        await client_bot.send_message(user_id, Validation.incorrect_input_quantity)


async def handle_question_fourth(filter_entity, msg, question_number, user_id, subscription_id):
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name
    if "DEPOP" in subscription_name or "POSHMARK" in subscription_name:
        if Validation.validate_date(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            await fifth_filter(user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_date)

    elif "GRAILED" in subscription_name or "SCHPOCK" in subscription_name \
            or "VINTED" in subscription_name or "WALLAPOP" in subscription_name:
        if Validation.validate_positive_integer(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            await fifth_filter(user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_quantity)


async def handle_question_fifth(filter_entity, msg, question_number, user_id, subscription_id):
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name
    if "DEPOP" in subscription_name:
        if Validation.validate_positive_integer(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            await preset_choose(user_id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_quantity)

    elif "GRAILED" in subscription_name or "SCHPOCK" in subscription_name \
            or "WALLAPOP" in subscription_name or "POSHMARK" in subscription_name or "VINTED" in subscription_name:
        if Validation.validate_date(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            if "POSHMARK" in subscription_name:
                await preset_choose(user_id)
            else:
                await sixth_filter(user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_date)


async def handle_question_sixth(filter_entity, msg, question_number, user_id, subscription_id):
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name
    if "DEPOP" in subscription_name or "POSHMARK" in subscription_name:
        if Validation.validate_yes_no(msg):
            question_number = 0
            await FilterDao.update(filter_entity.id, question_number=question_number)
            await preset_answer_handle(msg, user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_yes_or_no)

    elif "GRAILED" in subscription_name or "SCHPOCK" in subscription_name \
            or "WALLAPOP" in subscription_name:
        if Validation.validate_date(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            await seventh_filter(user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_date)

    elif "VINTED" in subscription_name:
        if Validation.validate_positive_integer(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            await preset_choose(user_id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_quantity)


async def handle_question_seventh(filter_entity, msg, question_number, user_id, subscription_id):
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name

    if "GRAILED" in subscription_name or "SCHPOCK" in subscription_name \
            or "WALLAPOP" in subscription_name:
        if Validation.validate_positive_integer(msg):
            value = filter_entity.value + msg + "\n"
            question_number += 1
            await FilterDao.update(filter_entity.id, value=value, question_number=question_number)
            await preset_choose(user_id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_quantity)

    elif "VINTED" in subscription_name:
        if Validation.validate_yes_no(msg):
            question_number = 0
            await FilterDao.update(filter_entity.id, question_number=question_number)
            await preset_answer_handle(msg, user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_yes_or_no)


async def handle_question_eighth(filter_entity, msg, question_number, user_id, subscription_id):
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name

    if "GRAILED" in subscription_name or "SCHPOCK" in subscription_name \
            or "WALLAPOP" in subscription_name:
        if Validation.validate_yes_no(msg):
            question_number = 0
            await FilterDao.update(filter_entity.id, question_number=question_number)
            await preset_answer_handle(msg, user_id, subscription_id, filter_entity.id)
        else:
            await client_bot.send_message(user_id, Validation.incorrect_input_yes_or_no)


async def main():
    await SubscriptionDao.add_subscriptions()
    await PaymentSystemDao.add_payment_systems()
    await client_bot.run_until_disconnected()
    await client_user_bitpapa.run_until_disconnected()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
