import logging

from aiogram import F, Router
from aiogram.types import Message

import database.repo as repo
import keyboards.keyboards as kb
from config import BOT_USERNAME
from services.codes import encode_referral

logger = logging.getLogger(__name__)
router = Router(name="user_referral")


@router.message(F.text == kb.BTN_REFERRAL)
async def referral_menu(message: Message):
    user = await repo.get_or_create_user(message.from_user.id)
    ref_count = await repo.get_referral_count(user["telegram_id"])
    bonus = await repo.get_int_setting("referral_bonus", 5000)
    enabled = (await repo.get_setting("referral_enabled", "1")) == "1"
    username = BOT_USERNAME or "bot"
    link = f"https://t.me/{username}?start={encode_referral(user['telegram_id'])}"

    text = (
        "🤝 Do'stlarni taklif qilish\n\n"
        f"💵 Balansingiz: {user.get('balance', 0):,} so'm\n\n"
        f"🔗 Sizning havolangiz:\n{link}\n\n"
        f"🤝 Taklif qilganlaringiz: {ref_count}\n"
        f"🎁 Har bir yangi do'st uchun: {bonus:,} so'm\n\n"
        "Ushbu balansni faqat bot ichidagi xizmatlar (e'lon, zakaz, kontakt) "
        "uchun ishlatishingiz mumkin."
    )
    if not enabled:
        text += "\n\n⚠️ Referal tizimi hozircha vaqtincha o'chirilgan."
    await message.answer(text)
