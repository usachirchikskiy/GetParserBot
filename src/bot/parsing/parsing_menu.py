import asyncio
import json

from telethon import Button, events
from telethon.tl.types import UpdateBotCallbackQuery, UpdateNewMessage

from src.bot.parsing.parsing_site import handle_site
from src.database.dao.Associations import UserSubscriptionDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.database.dao.UserDao import UserDao
from src.main import client_bot
from src.utils.constants import media, sites, total_pages
from src.utils.utils import flag, description_of_area


def pagination_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "previous" in data or "next" in data \
            or "page_total" in data or "favourite_subscription_list" in data:
        return True


def subscription_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "action" in data:
        action = data['action']
        flattened_sites = [item for sublist in sites for item in sublist]
        return action in flattened_sites


def subscription_buy_callback_filter(event):
    data = json.loads(event.data)
    if not isinstance(data, dict):
        return False
    for subscription_title in data.keys():
        if subscription_title.split(".")[0] in ["DEPOP", "GRAILED", "POSHMARK", "SCHPOCK", "VINTED", "WALLAPOP"]:
            return True
    return False


async def handle_begin_parsing(event, page=1):
    buttons = [
        [Button.inline(f"{site[i]}", data=json.dumps({"action": f"{site[i]}"})) for i in range(len(site))]
        for site in sites[(page - 1) * 7:page * 7]
    ]
    pagination_buttons = [
        Button.inline("◀", data=json.dumps({"previous": page})),
        Button.inline(f"{page}/{total_pages}", data=json.dumps({"page_total": ""})),
        Button.inline("▶", data=json.dumps({"next": page})),
    ]
    favourite_button = [
        Button.inline("⭐ Избранное", data=json.dumps({"favourite_subscription_list": ""}))
    ]
    back_button = [
        Button.inline("Назад", data=json.dumps({"action": "back_to_main_menu"})),
    ]
    buttons.append(pagination_buttons)
    buttons.append(favourite_button)
    buttons.append(back_button)
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите площадку",
                                  buttons=buttons)


async def check_user_subscription(event, subscription_title):
    user_id = event.original_update.user_id
    subscription = await SubscriptionDao.find_one_or_none(name=subscription_title)
    if subscription:
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
            ],
            [
                Button.inline("Назад", data=json.dumps({"action": "begin_parsing"})),
            ]
        ]
        if not is_subscription_active:
            return buttons
    return None


async def handle_favourite_subscription_list(event, chunked_subscriptions, favourite_total, page=1):
    buttons = [
        [Button.inline(
            f"{flag(subscription[i]['Subscription'].name.split('.')[1])}{subscription[i]['Subscription'].name}",
            data=json.dumps({
                "action": f"{flag(subscription[i]['Subscription'].name.split('.')[1])} {subscription[i]['Subscription'].name}"}))
            for i in range(len(subscription))]
        for subscription in chunked_subscriptions[(page - 1) * 7:page * 7]
    ]
    pagination_buttons = [
        Button.inline("◀", data=json.dumps({"previous_favourite": page})),
        Button.inline(f"{page}/{favourite_total}", data=json.dumps({"page_total": ""})),
        Button.inline("▶", data=json.dumps({"next_favourite": page})),
    ]
    back_button = [
        Button.inline("Назад", data=json.dumps({"action": "begin_parsing"})),
    ]
    buttons.append(pagination_buttons)
    buttons.append(back_button)
    await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "Выберите площадку",
                                  buttons=buttons)


@client_bot.on(events.CallbackQuery(func=pagination_callback_filter))
async def subscription_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    if "previous" in data:
        page = data['previous']
        if page > 1:
            page -= 1
            await handle_begin_parsing(event, page=page)
    elif "next" in data:
        page = data['next']
        if page < total_pages:
            page += 1
            await handle_begin_parsing(event, page=page)
    elif "favourite_subscription_list" in data:
        subscriptions = await favourite_subscription_list(event.chat_id)
        if len(subscriptions) == 0:
            await event.answer('❌ У вас нет избранных подписок', alert=True)
        else:
            chunked_subscriptions = [subscriptions[i:i + 2] for i in range(0, len(subscriptions), 2)]
            favourite_total = len(chunked_subscriptions)
            await handle_favourite_subscription_list(event, chunked_subscriptions, favourite_total)


@client_bot.on(events.CallbackQuery(func=subscription_callback_filter))
async def subscription_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    action = data['action']
    subscription_title = action.split(" ")[1]

    has_subscription = await UserSubscriptionDao.exists(user_id=event.chat_id)
    if has_subscription:
        await handle_site(subscription_title, event)
    else:
        await get_buttons_for_payment(event, subscription_title, action)

    # Todo apply separate subscriptions
    # buttons = await check_user_subscription(event, subscription_title)
    # if buttons:
    #     message = description_of_area(subscription_title)
    #     await client_bot.send_file(event.chat_id, caption=action + "\n" + message, file=media,
    #                                buttons=buttons)
    # else:
    # await handle_site(subscription_title, event)


async def get_buttons_for_payment(event, subscription_title, action):
    subscription = await SubscriptionDao.find_one_or_none(name=subscription_title)
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
        ],
        [
            Button.inline("Назад", data=json.dumps({"action": "begin_parsing"})),
        ]
    ]
    message = description_of_area(subscription_title)
    await client_bot.send_file(event.chat_id, caption=action + "\n" + message, file=media,
                               buttons=buttons)


@client_bot.on(events.CallbackQuery(func=subscription_buy_callback_filter))
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
    # task = asyncio.create_task(UserSubscriptionDao.add_or_update_all(value[1], user_id=user_id))
    # task.add_done_callback(handle_exception)
    await UserSubscriptionDao.add_or_update_all(value[1], user_id=user_id)
    # Todo apply separate subscription
    # subscription_id = (await SubscriptionDao.find_one_or_none(name=key)).id
    # await UserSubscriptionDao.add_or_update(value[1], user_id=user_id, subscription_id=subscription_id)
    return True


async def favourite_subscription_list(user_id):
    user_subscriptions = await UserSubscriptionDao.find_all(user_id=user_id, is_favourite=True)
    subscriptions_ids = [subscription.subscription_id for subscription in user_subscriptions]
    subscriptions = await SubscriptionDao.find_by_ids(*subscriptions_ids)
    return subscriptions
