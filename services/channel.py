"""Kanalga post joylash / o'chirish bilan bog'liq umumiy funksiyalar."""
import logging
from datetime import datetime

import config
import database.repo as repo
import keyboards.keyboards as kb

logger = logging.getLogger(__name__)


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


async def _post_text(item: dict) -> str:
    body = (item.get("caption") or item.get("text") or "").strip()
    sign = await repo.get_setting("sign_text") or repo.SIGN_DEFAULT
    return f"{body}\n\n{sign}\n\n🆔 {item['public_code']}"


async def publish_ad(bot, ad: dict):
    if not config.CHANNEL_ID:
        logger.warning("CHANNEL_ID sozlanmagan — e'lon kanalga joylanmadi.")
        return None
    text = await _post_text(ad)
    markup = kb.ad_channel_kb(ad["public_code"])
    try:
        if ad["message_type"] == "PHOTO" and ad["telegram_file_id"]:
            msg = await bot.send_photo(config.CHANNEL_ID, ad["telegram_file_id"],
                                        caption=text, reply_markup=markup)
        else:
            msg = await bot.send_message(config.CHANNEL_ID, text, reply_markup=markup)
    except Exception:
        logger.exception("E'lonni kanalga joylashda xato: %s", ad["public_code"])
        return None
    await repo.update_ad(ad["id"], channel_message_id=msg.message_id,
                          status="PUBLISHED", published_at=_now())
    return msg.message_id


async def publish_order(bot, order: dict):
    if not config.CHANNEL_ID:
        logger.warning("CHANNEL_ID sozlanmagan — zakaz kanalga joylanmadi.")
        return None
    text = await _post_text(order)
    markup = kb.order_channel_kb(order["public_code"])
    try:
        if order["message_type"] == "PHOTO" and order["telegram_file_id"]:
            msg = await bot.send_photo(config.CHANNEL_ID, order["telegram_file_id"],
                                        caption=text, reply_markup=markup)
        else:
            msg = await bot.send_message(config.CHANNEL_ID, text, reply_markup=markup)
    except Exception:
        logger.exception("Zakazni kanalga joylashda xato: %s", order["public_code"])
        return None
    await repo.update_order(order["id"], channel_message_id=msg.message_id,
                             status="PUBLISHED", published_at=_now())
    return msg.message_id


async def delete_channel_post(bot, message_id):
    if not (config.CHANNEL_ID and message_id):
        return
    try:
        await bot.delete_message(config.CHANNEL_ID, message_id)
    except Exception:
        logger.warning("Kanal postini o'chirib bo'lmadi: %s", message_id)
