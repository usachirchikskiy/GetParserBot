import json

from telethon import Button, events

from src.bot.parsing.parsing_site import handle_site
from src.database.dao.Associations import UserSubscriptionDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.database.dao.UserDao import UserDao
from src.main import client_bot
from src.utils.constants import depop, media, sites


# TODO(add previous next buttons)


def subscription_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        flattened_sites = [item for sublist in sites for item in sublist]
        return action in flattened_sites


def subscription_buy_filter(event):
    data = json.loads(event.data)
    if not isinstance(data, dict):
        return False
    for subscription_title in data.keys():
        if subscription_title.split(".")[0] in ["DEPOP", "GRAILED", "SCHPOCK"]:
            return True
    return False


async def handle_begin_parsing(event):
    buttons = [[Button.inline(f"{site[i]}", data=json.dumps({"action": f"{site[i]}"})) for i in range(2)]
               for site in sites]

    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите площадку",
                                  buttons=buttons)


async def check_user_subscription(event, subscription_title):
    user_id = event.original_update.user_id
    subscription = await SubscriptionDao.find_one_or_none(name=subscription_title)
    subscription_id = subscription.id
    is_subscription_active = await UserSubscriptionDao.is_active(user_id=user_id, subscription_id=subscription_id)
    buttons = [
        [
            Button.inline(f"Купить на 30 дней [{subscription.price_month} RUB]",
                          data=json.dumps({f"{subscription_title}": [subscription.price_month, 30]}))
        ],
        [
            Button.inline(f"Купить на 7 дней [{subscription.price_week} RUB]",
                          data=json.dumps({f"{subscription_title}": [subscription.price_week, 7]}))
        ],
        [
            Button.inline(f"Купить на 3 дня [{subscription.price_three_day} RUB]",
                          data=json.dumps({f"{subscription_title}": [subscription.price_three_day, 3]}))
        ],
        [
            Button.inline(f"Купить на 1 день [{subscription.price_one_day} RUB]",
                          data=json.dumps({f"{subscription_title}": [subscription.price_one_day, 1]}))
        ]
    ]
    if not is_subscription_active:
        return buttons
    return None


@client_bot.on(events.CallbackQuery(func=subscription_callback_filter))
async def subscription_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    subscription_title = action.split(" ")[1]
    buttons = await check_user_subscription(event, subscription_title)
    if buttons:
        await client_bot.send_file(event.chat_id, caption=action + "\n" + depop, file=media,
                                   buttons=buttons)
    else:
        await handle_site(subscription_title, event)


@client_bot.on(events.CallbackQuery(func=subscription_buy_filter))
async def subscription_buy_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    key = next(iter(data.keys()))
    value = data[key]
    user_id = event.original_update.user_id
    purchased = await handle_subscription_purchase(key, value, user_id)
    if not purchased:
        buttons = [[Button.inline("Назад", data=json.dumps({"action": "back_to_main_menu"}))]]
        await client_bot.send_file(event.chat_id, caption="На вашем балансе недостаточно средств", file=media,
                                   buttons=buttons)
    else:
        await handle_site(key, event)


async def handle_subscription_purchase(key, value, user_id):
    user_balance = (await UserDao.find_one_or_none(id=user_id)).balance
    if user_balance < value[0]:
        return False
    user_balance_updated = user_balance - value[0]
    await UserDao.update(user_id, balance=user_balance_updated)
    subscription_id = (await SubscriptionDao.find_one_or_none(name=key)).id
    await UserSubscriptionDao.add_or_update(value[1], user_id=user_id, subscription_id=subscription_id)
    return True
