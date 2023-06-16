import json

from telethon import events, Button

from src.bot.parsing.sites.runner import run_parsing
from src.database.dao.Associations import UserFilterSubscriptionDao
from src.database.dao.FilterDao import FilterDao
from src.database.dao.SubscriptionDao import SubscriptionDao
from src.main import client_bot
from src.utils.constants import media


def run_or_delete_preset_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "preset_run" in data or "preset_delete" in data:
        return True


def delete_all_presets_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "delete_all" in data:
        return True


def saved_presets_callback_filter(event):
    data = json.loads(event.data.decode("utf-8"))
    if "user_filter_subscription_id" in data:
        return True


@client_bot.on(events.CallbackQuery(func=saved_presets_callback_filter))
async def saved_presets_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    id = data['user_filter_subscription_id']
    user_filter_subscription = (await UserFilterSubscriptionDao.find_one_or_none(id=id))
    subscription_title = (
        await (SubscriptionDao.find_one_or_none(id=user_filter_subscription.subscription_id))).name
    filter_id = user_filter_subscription.filter_id
    filter_entity = await FilterDao.find_one_or_none(id=filter_id)
    buttons = [
        [Button.inline(f"🔍 Запустить", data=json.dumps({
            "preset_run": [filter_id, user_filter_subscription.subscription_id]
        }))],
        [Button.inline(f"Удалить пресет", data=json.dumps({
            "preset_delete": [filter_id, subscription_title]
        }
        ))],
        [Button.inline(f"Назад", data=json.dumps({"action": f"presets {subscription_title}"}))]
    ]
    await client_bot.send_file(event.chat_id,
                               caption="Ваш пресет:" + user_filter_subscription.title + "\n" + filter_entity.value,
                               file=media,
                               buttons=buttons)


@client_bot.on(events.CallbackQuery(func=delete_all_presets_callback_filter))
async def delete_all_presets_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    subscription_id = int(data['delete_all'])
    user_filter_subscriptions = await UserFilterSubscriptionDao.find_all(user_id=event.chat_id,
                                                                         subscription_id=subscription_id)
    ids_to_delete = [filter_entity.filter_id for filter_entity in
                     user_filter_subscriptions]
    await FilterDao.delete_by_ids(ids_to_delete)


@client_bot.on(events.CallbackQuery(func=run_or_delete_preset_callback_filter))
async def run_or_delete_preset_callback_handler(event):
    data = json.loads(event.data.decode("utf-8"))
    if 'preset_delete' in data:
        filter_id = data["preset_delete"][0]
        subscription_title = data["preset_delete"][1]
        await FilterDao.delete(id=filter_id)
        buttons = [
            [Button.inline(f"Назад", data=json.dumps({"action": f"presets {subscription_title}"}))]
        ]
        await client_bot.edit_message(event.chat_id, event.original_update.msg_id, "❌ Пресет удален", buttons=buttons)

    elif 'preset_run' in data:
        user_id = event.chat_id
        filter_id = data["preset_run"][0]
        subscription_id = data["preset_run"][1]
        await run_parsing(user_id, subscription_id, filter_id)


async def presets(user_id, subscription_id):
    message = "Сохраненные пресеты"
    titles = await UserFilterSubscriptionDao.find_all(user_id=user_id, subscription_id=subscription_id,
                                                      is_favourite=True)
    buttons = []
    for title in titles:
        button = [Button.inline(f"{title.title}", data=json.dumps({"user_filter_subscription_id": title.id}))]
        buttons.append(button)
    subscription_name = (await SubscriptionDao.find_one_or_none(id=subscription_id)).name
    buttons.append([Button.inline("Удалить все", data=json.dumps({"delete_all": f"{subscription_id}"}))])
    buttons.append([Button.inline("Назад", data=json.dumps({"action": f"back_to_handle_site {subscription_name}"}))])
    await client_bot.send_file(user_id, caption=message, file=media,
                               buttons=buttons)
