"""E'lon / Zakaz / Kontakt-unlock uchun umumiy to'lov oqimi yordamchisi."""

import database.repo as repo
import keyboards.keyboards as kb


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
