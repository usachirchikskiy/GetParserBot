import asyncio
import json
from telethon import Button, events

from src.bot.parsing.parsing_site import second_filter, third_filter, fifth_filter, \
    preset_answer_handle, fourth_filter, preset_choose, run_parsing
from src.database.dao.Associations import UserPaymentSystemDao, UserFilterSubscriptionDao
from src.database.dao.FilterDao import FilterDao
from src.database.dao.PaymentSystemDao import PaymentSystemDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.main import client_bot, client_user_bitpapa
from src.database.dao.UserDao import UserDao

from src.bot.parsing.parsing_menu import handle_begin_parsing
from src.bot.top_up.bit_papa import check_input_bit_papa
from src.bot.top_up.crypto_bot import check_input_crypto_bot
from src.bot.top_up.top_up_menu import handle_top_up
from src.utils.constants import media, parsing_tasks
from src.utils.validation import Validation


def menu_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        return action in ["begin_parsing", "top_up", "profile", "tech_support",
                          "referral_system", "settings", "back_to_main_menu"]


async def menu(event, from_callback):
    try:
        id = event.original_update.message.peer_id.user_id
    except Exception as e:
        id = event.original_update.user_id

    user = await UserDao.find_one_or_none(id=id)

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


@client_bot.on(events.CallbackQuery(func=menu_callback_filter))
async def menu_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    if action == "begin_parsing":
        await handle_begin_parsing(event)
    elif action == "top_up":
        await handle_top_up(event)
    elif action == "profile":
        pass
        # await handle_profile(event)
    elif action == "tech_support":
        pass
        # await handle_technical_support(event)
    elif action == "referral_system":
        pass
        # await handle_referral_system(event)
    elif action == "settings":
        pass
    elif action == "back_to_main_menu":
        await menu(event, True)
        # await handle_settings(event)


### Handle Text and Start command
@client_bot.on(events.NewMessage(pattern=r'^(?!/start).*$'))
async def user_input_handler(event):
    user_id = event.original_update.message.peer_id.user_id
    await handle_payment(event, user_id)
    await handle_message(event)


@client_bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.original_update.message.peer_id.user_id
    user = await UserDao.find_one_or_none(id=user_id)
    if user is None:
        await UserDao.add(id=user_id, balance=0.0)
    await menu(event, False)


async def handle_payment(event, user_id):
    user_payment_system = await UserPaymentSystemDao.find_one_or_none(user_id=user_id)
    if user_payment_system is not None:
        payment_system_id = user_payment_system.payment_system_id
        if payment_system_id == 1:
            await check_input_bit_papa(event)
        elif payment_system_id == 2:
            await check_input_crypto_bot(event)
        elif payment_system_id == 3:
            pass
        elif payment_system_id == 4:
            pass


async def handle_message(event):
    user_id = event.original_update.message.peer_id.user_id
    userFilterSubscription = await UserFilterSubscriptionDao.get_last_added(user_id)
    msg = event.raw_text
    last_bot_message = (await UserDao.find_one_or_none(id=user_id)).bot_message
    if last_bot_message == "Введите название для пресета":
        await UserFilterSubscriptionDao.update(userFilterSubscription.id,
                                               is_favourite=True,
                                               title=msg)
        await UserDao.update(user_id, bot_message="Nothing")
        await run_parsing(user_id, userFilterSubscription.subscription_id, userFilterSubscription.filter_id)

    if msg == "Остановить парсер":
        if user_id in parsing_tasks and not parsing_tasks[user_id].done():
            parsing_tasks[user_id].cancel()
            del parsing_tasks[user_id]
            await client_bot.send_message(user_id, "Парсер остановлен")

    if userFilterSubscription:
        subscription_id = userFilterSubscription.subscription_id
        filter_id = userFilterSubscription.filter_id
        filter_entity = await FilterDao.find_one_or_none(id=filter_id)
        question_number = filter_entity.question_number
        if question_number == 1:
            if Validation.check_url_contains_domain(msg.split(","), r'depop.com'):
                value = filter_entity.value + msg + "\n"
                question_number += 1
                await FilterDao.update(filter_id, value=value, question_number=question_number)
                await second_filter(user_id, subscription_id, filter_id)
            else:
                await client_bot.send_message(user_id, Validation.incorrect_input_words_links)
        elif question_number == 2:
            if Validation.validate_price_range(msg):
                value = filter_entity.value + msg + "\n"
                question_number += 1
                await FilterDao.update(filter_id, value=value, question_number=question_number)
                await third_filter(user_id, subscription_id, filter_id)
            else:
                await client_bot.send_message(user_id, Validation.incorrect_input_price_range)
        elif question_number == 3:
            if Validation.validate_positive_integer(msg):
                value = filter_entity.value + msg + "\n"
                question_number += 1
                await FilterDao.update(filter_id, value=value, question_number=question_number)
                await fourth_filter(user_id, subscription_id, filter_id)
            else:
                await client_bot.send_message(user_id, Validation.incorrect_input_quantity)
        elif question_number == 4:
            if Validation.validate_positive_integer(msg, True):
                value = filter_entity.value + msg + "\n"
                question_number += 1
                await FilterDao.update(filter_id, value=value, question_number=question_number)
                await fifth_filter(user_id, subscription_id, filter_id)
            else:
                await client_bot.send_message(user_id, Validation.incorrect_input_quantity)
        elif question_number == 5:
            if Validation.validate_date(msg):
                value = filter_entity.value + msg + "\n"
                question_number += 1
                await FilterDao.update(filter_id, value=value, question_number=question_number)
                await preset_choose(user_id)
            else:
                await client_bot.send_message(user_id, Validation.incorrect_input_date)
        elif question_number == 6:
            if Validation.validate_yes_no(msg):
                question_number = 0
                await FilterDao.update(filter_id, question_number=question_number)
                await preset_answer_handle(msg, user_id, subscription_id, filter_id)
            else:
                await client_bot.send_message(user_id, Validation.incorrect_input_yes_or_no)



async def main():
    await SubscriptionDao.add_subscriptions()
    await PaymentSystemDao.add_payment_systems()
    await client_bot.run_until_disconnected()
    await client_user_bitpapa.run_until_disconnected()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
