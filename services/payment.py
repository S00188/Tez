"""E'lon / Zakaz / Kontakt-unlock uchun umumiy to'lov oqimi yordamchisi."""

<<<<<<< HEAD
import database.repo as repo
import keyboards.keyboards as kb

=======
import logging

import database.repo as repo
import keyboards.keyboards as kb

logger = logging.getLogger(__name__)

>>>>>>> 963967d (Render deploy uchun tayyor)

async def offer_payment(message, price: int, prefix: str):
    """Foydalanuvchiga balansi yetarli/yetarli emasligiga qarab tugmalar
    bilan to'lov taklifini ko'rsatadi."""
    balance = await repo.get_balance(message.from_user.id)
    if balance >= price:
        await message.answer(
            f"💳 To'lov qilish\n\n"
            f"Sizning balansingizda {balance:,} so'm mavjud.\n"
            f"Xizmat narxi: {price:,} so'm.\n\n"
            f"To'lov usulini tanlang:",
            reply_markup=kb.payment_choice_kb(prefix))
    else:
        card = await repo.get_setting("card_number") or "—"
        holder = await repo.get_setting("card_holder") or "—"
        await message.answer(
            f"💳 To'lov qilish\n\n"
            f"To'lov qilish uchun quyidagi karta raqamiga {price:,} so'm "
            f"o'tkazing, so'ngra chek rasmini shu yerga yuboring 👇\n\n"
            f"👤 Karta egasi: {holder}\n"
            f"💳 {card}",
            reply_markup=kb.pay_card_only_kb())
<<<<<<< HEAD
=======


async def maybe_notify_referral_bonus(bot, telegram_id):
    """Foydalanuvchi birinchi marta muvaffaqiyatli to'lov qilganda referal
    bonusini (agar u kimningdir taklifi orqali kelgan bo'lsa va hali
    bonus berilmagan bo'lsa) beradi va referrerga xabar yuboradi. Har bir
    to'lov tasdiqlanish nuqtasidan (balansdan/karta orqali, admin
    tasdig'idan keyin) chaqirilishi kerak."""
    bonus = await repo.get_int_setting("referral_bonus", 5000)
    referral_on = (await repo.get_setting("referral_enabled", "1")) == "1"
    if not referral_on:
        return
    user = await repo.get_user(telegram_id)
    if not user or not user.get("referred_by"):
        return
    granted = await repo.try_grant_referral_bonus(telegram_id, bonus)
    if not granted:
        return
    await repo.log_admin_action(
        None, "REFERRAL_BONUS", "user", str(user["referred_by"]),
        f"+{bonus} so'm, taklif qilingan: {telegram_id} (birinchi to'lov)")
    try:
        await bot.send_message(
            user["referred_by"],
            f"🤝 Siz taklif qilgan foydalanuvchi birinchi to'lovni amalga "
            f"oshirdi!\n🎁 Balansingizga {bonus:,} so'm qo'shildi.")
    except Exception:
        logger.warning("Referal bonus xabari yuborilmadi: %s", user["referred_by"])

>>>>>>> 963967d (Render deploy uchun tayyor)
