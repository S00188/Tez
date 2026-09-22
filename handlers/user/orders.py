import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database.repo as repo
import keyboards.keyboards as kb
<<<<<<< HEAD
from services.payment import offer_payment
from services.channel import publish_order
=======
from services.payment import offer_payment, maybe_notify_referral_bonus
from services.channel import publish_order
from services.flow import abandon_pending_flow
from services.locks import get_lock
>>>>>>> 963967d (Render deploy uchun tayyor)
from states import OrderStates, UnlockStates

logger = logging.getLogger(__name__)
router = Router(name="user_orders")


# ============================================================
#  ZAKAZ BERISH (foydalanuvchi tomonidan)
# ============================================================
@router.message(Command("order"))
@router.message(F.text == kb.BTN_ORDER)
async def order_begin(message: Message, state: FSMContext):
<<<<<<< HEAD
=======
    # Yarim qolgan to'lanmagan zakaz bo'lsa CANCELLED qilinadi — aks holda
    # abadiy "faol" bo'lib qolib kvotani band qilib turadi.
    await abandon_pending_flow(state)
    await repo.expire_stale_pending()
>>>>>>> 963967d (Render deploy uchun tayyor)
    user = await repo.get_or_create_user(message.from_user.id)
    active = await repo.count_user_active_orders(user["telegram_id"])
    max_active = await repo.get_int_setting("max_active_orders", 5)
    if active >= max_active:
        await message.answer(
            f"⛔️ Faol zakazlar soni limitga yetdi ({max_active} ta). "
            "Avval eskisini yakunlang.",
            reply_markup=kb.main_menu_rb(await repo.is_admin(message.from_user.id)))
        return
    await state.set_state(OrderStates.awaiting_content)
    guide = await repo.get_setting("order_guide") or "🔵 Dasturga zakaz berish"
    await message.answer(guide, reply_markup=kb.order_guarantee_kb())


@router.callback_query(F.data == "order:guarantee")
async def order_guarantee(cq: CallbackQuery):
    text = await repo.get_setting("order_guarantee") or "❓ Kafolat matni yo'q."
    await cq.answer()
    await cq.message.answer(text, reply_markup=kb.guarantee_info_kb())


async def _create_order_and_offer(message: Message, state: FSMContext,
                                   message_type, file_id, caption, text):
    user = await repo.get_or_create_user(message.from_user.id)
    order_id, code = await repo.create_order(
        user_id=user["telegram_id"], message_type=message_type,
        telegram_file_id=file_id, caption=caption, text=text,
        status="WAITING_PAYMENT")
    await state.update_data(kind="order", item_id=order_id, public_code=code)
    price = await repo.get_int_setting("order_price", 34990)
    await message.answer(
        f"🔵 Zakazingiz tayyor!\n\n"
        f"🆔 Zakaz raqami: {code}\n\n"
        f"Zakazni kanalimizga joylashtirish narxi {price:,} so'm.\n"
        f"Iltimos, to'lovni amalga oshiring.")
    await offer_payment(message, price, "order")


@router.message(OrderStates.awaiting_content, F.photo)
async def order_content_photo(message: Message, state: FSMContext):
    await _create_order_and_offer(
        message, state, "PHOTO", message.photo[-1].file_id,
        message.caption or "", None)


@router.message(OrderStates.awaiting_content, F.text)
async def order_content_text(message: Message, state: FSMContext):
    await _create_order_and_offer(
        message, state, "TEXT", None, None, message.text)


@router.callback_query(F.data == "order:pay_balance")
async def order_pay_balance(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("item_id")
    order = await repo.get_order(order_id) if order_id else None
    if not order or order["status"] != "WAITING_PAYMENT":
        await cq.answer("Bu zakaz topilmadi yoki allaqachon qayta ishlangan.",
                         show_alert=True)
        return
    price = await repo.get_int_setting("order_price", 34990)
    balance = await repo.get_balance(cq.from_user.id)
    if balance < price:
        await cq.answer("Balansingiz yetarli emas.", show_alert=True)
        return
<<<<<<< HEAD
    await repo.add_balance(cq.from_user.id, -price)
    await repo.create_payment(user_id=cq.from_user.id, ptype="ORDER_PUBLICATION",
                               amount=price, order_id=order_id, status="APPROVED")
    msg_id = await publish_order(cq.bot, await repo.get_order(order_id))
=======

    # Atomik compare-and-swap — tugmani ikki marta tez bosishdan himoya
    # (balans ikki marta yechilishi / zakaz kanalga ikki marta
    # joylashtirilishining oldini oladi).
    locked = await repo.cas_update_status("orders", order_id, "WAITING_PAYMENT",
                                           status="PROCESSING")
    if not locked:
        await cq.answer("Bu zakaz allaqachon qayta ishlanmoqda.", show_alert=True)
        return

    await repo.add_balance(cq.from_user.id, -price)
    await repo.create_payment(user_id=cq.from_user.id, ptype="ORDER_PUBLICATION",
                               amount=price, order_id=order_id, status="APPROVED")
    await maybe_notify_referral_bonus(cq.bot, cq.from_user.id)
    msg_id = await publish_order(cq.bot, await repo.get_order(order_id))
    if not msg_id:
        await repo.update_order(order_id, status="WAITING_ADMIN")
>>>>>>> 963967d (Render deploy uchun tayyor)
    await state.clear()
    await cq.answer("✅ To'landi!")
    if msg_id:
        await cq.message.edit_text(
            "✅ Zakazingiz tasdiqlandi!\n\n📢 Zakazingiz kanalga joylashtirildi.\n\n"
            "Rahmat! ❤️")
    else:
        await cq.message.edit_text(
            "✅ To'lov qabul qilindi, lekin kanalga joylashda texnik xatolik "
            "yuz berdi. Admin tez orada ko'rib chiqadi.")


@router.callback_query(F.data == "order:pay_card")
async def order_pay_card(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("item_id")
    order = await repo.get_order(order_id) if order_id else None
    if not order or order["status"] != "WAITING_PAYMENT":
        await cq.answer("Bu zakaz topilmadi yoki allaqachon qayta ishlangan.",
                         show_alert=True)
        return
<<<<<<< HEAD
    await repo.update_order(order_id, status="WAITING_RECEIPT")
=======
    locked = await repo.cas_update_status("orders", order_id, "WAITING_PAYMENT",
                                           status="WAITING_RECEIPT")
    if not locked:
        await cq.answer("Bu zakaz allaqachon qayta ishlanmoqda.", show_alert=True)
        return
>>>>>>> 963967d (Render deploy uchun tayyor)
    await state.set_state(OrderStates.awaiting_receipt)
    await cq.answer()
    await cq.message.answer(
        "📎 Chekni yuboring\n\nTo'lovni amalga oshirgach, chek rasmini shu "
        "chatga yuboring.\n⚠️ Chekdagi summa ko'rinib turishi kerak.",
        reply_markup=kb.cancel_kb())


@router.message(OrderStates.awaiting_receipt, F.photo)
async def order_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("item_id")
    code = data.get("public_code")
    order = await repo.get_order(order_id) if order_id else None
    if not order:
        await state.clear()
        await message.answer("Xatolik: zakaz topilmadi.",
                              reply_markup=kb.main_menu_rb(await repo.is_admin(message.from_user.id)))
        return

    receipt_file_id = message.photo[-1].file_id
    dup = await repo.find_approved_payment_by_receipt(receipt_file_id)
    price = await repo.get_int_setting("order_price", 34990)
    payment_id = await repo.create_payment(
        user_id=message.from_user.id, ptype="ORDER_PUBLICATION", amount=price,
        order_id=order_id, status="WAITING_ADMIN")
    await repo.update_payment(payment_id, receipt_file_id=receipt_file_id)
    await repo.update_order(order_id, status="WAITING_ADMIN")
    await state.clear()

    await message.answer(
        "✅ Chek qabul qilindi! Admin tasdiqlagach zakazingiz kanalga "
        f"joylanadi.\n\n🆔 Kod: {code}",
        reply_markup=kb.main_menu_rb(await repo.is_admin(message.from_user.id)))

    warn = ("\n\n⚠️ DIQQAT: bu chek rasmi ilgari tasdiqlangan boshqa to'lovda "
            "ham ishlatilgan bo'lishi mumkin!") if dup else ""
    for admin_id in await repo.list_admin_ids():
        try:
            await message.bot.send_photo(
                chat_id=admin_id, photo=receipt_file_id,
                caption=(
                    f"🔵 YANGI ZAKAZ\n\n"
                    f"👤 Foydalanuvchi: @{message.from_user.username or '—'}\n"
                    f"🆔 User ID: {message.from_user.id}\n\n"
                    f"🆔 Zakaz: {code}\n"
                    f"💰 Summa: {price:,} so'm{warn}"),
                reply_markup=kb.receipt_admin_kb(payment_id))
        except Exception:
            logger.warning("Admin (%s) ga xabar yuborilmadi", admin_id)


@router.message(OrderStates.awaiting_receipt)
async def order_receipt_wrong(message: Message):
    await message.answer("📎 Iltimos, to'lov chekini rasm ko'rinishida yuboring.",
                          reply_markup=kb.cancel_kb())


# ============================================================
#  DEVELOPER: "📩 Men buni qila olaman" — kanaldagi tugma
# ============================================================
@router.callback_query(F.data.startswith("order:apply:"))
async def order_apply(cq: CallbackQuery):
    code = cq.data.split(":", 2)[2]
    order = await repo.get_order_by_code(code)
    await cq.answer()
    if not order or order["status"] not in ("PUBLISHED",):
        try:
            await cq.bot.send_message(cq.from_user.id, "❌ Bu zakaz endi mavjud emas.")
        except Exception:
            pass
        return
    if order["user_id"] == cq.from_user.id:
        try:
            await cq.bot.send_message(cq.from_user.id,
                                       "Bu — sizning o'z zakazingiz 🙂")
        except Exception:
            pass
        return

    unlocked = await repo.get_approved_unlock(order["id"], cq.from_user.id)
    price = await repo.get_int_setting("contact_price", 25000)
    body = order.get("text") or order.get("caption") or ""
    text = (f"🔵 ZAKAZ — {code}\n\n{body}\n\n"
            f"⚠️ Kontakt narxi: {price:,} so'm\n"
            f"⚠️ Zakaz muvaffaqiyatli bajarilishiga kafolat yo'q — bu aloqa "
            f"o'rnatuvchi vosita.")
    if unlocked:
        owner = await repo.get_user(order["user_id"])
        uname = f"@{owner['username']}" if owner and owner.get("username") else "—"
        text += f"\n\n👤 Buyurtmachi kontakti: {uname} (id: {order['user_id']})"
    try:
        await cq.bot.send_message(cq.from_user.id, text,
                                   reply_markup=kb.developer_order_kb(code, bool(unlocked)))
    except Exception:
        logger.warning("Developerga xabar yuborib bo'lmadi: %s", cq.from_user.id)


<<<<<<< HEAD
async def on_developer_ack(message: Message, code: str):
    """/start orqali ham chaqirilishi mumkin (kelajakda kerak bo'lsa)."""
    order = await repo.get_order_by_code(code)
    if not order:
        await message.answer("❌ Bunday zakaz topilmadi.")
        return
    await message.answer(
        f"🔵 ZAKAZ — {code}\n\n{order.get('text') or order.get('caption') or ''}",
        reply_markup=kb.developer_order_kb(code, False))


=======
>>>>>>> 963967d (Render deploy uchun tayyor)
# ============================================================
#  KONTAKTNI OCHISH (developer to'lovi)
# ============================================================
@router.callback_query(F.data.startswith("unlock:start:"))
async def unlock_start(cq: CallbackQuery, state: FSMContext):
    code = cq.data.split(":", 2)[2]
    order = await repo.get_order_by_code(code)
    await cq.answer()
    if not order:
        await cq.message.answer("❌ Zakaz topilmadi.")
        return
<<<<<<< HEAD
    if order["status"] == "COMPLETED":
        await cq.message.answer("❌ Bu zakaz allaqachon yopilgan — kontakt olib bo'lmaydi.")
=======
    if order["status"] != "PUBLISHED":
        # Avval faqat "COMPLETED" rad etilardi — ya'ni allaqachon
        # o'chirilgan/rad etilgan/bekor qilingan zakaz uchun ham eski
        # kanal xabaridagi tugma orqali kontakt to'lovi qilib qo'yish
        # mumkin edi. Endi faqat hali PUBLISHED bo'lgan zakazlar uchun
        # kontakt sotib olishga ruxsat beriladi.
        await cq.message.answer("❌ Bu zakaz endi mavjud emas — kontakt olib bo'lmaydi.")
>>>>>>> 963967d (Render deploy uchun tayyor)
        return
    if order["user_id"] == cq.from_user.id:
        return
    already = await repo.get_approved_unlock(order["id"], cq.from_user.id)
    if already:
        owner = await repo.get_user(order["user_id"])
        uname = f"@{owner['username']}" if owner and owner.get("username") else "—"
        await cq.message.answer(f"👤 Kontakt: {uname} (id: {order['user_id']})")
        return
    pending = await repo.has_pending_unlock(order["id"], cq.from_user.id)
    if pending:
        await cq.message.answer("⏳ Siz allaqachon to'lov yubordingiz, admin tekshirmoqda.")
        return

    price = await repo.get_int_setting("contact_price", 25000)
    await state.update_data(kind="unlock", order_id=order["id"], public_code=code)
    await offer_payment(cq.message, price, "unlock")


@router.callback_query(F.data == "unlock:pay_balance")
async def unlock_pay_balance(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    order = await repo.get_order(order_id) if order_id else None
    if not order:
        await cq.answer("Zakaz topilmadi.", show_alert=True)
        return
<<<<<<< HEAD
    price = await repo.get_int_setting("contact_price", 25000)
    balance = await repo.get_balance(cq.from_user.id)
    if balance < price:
        await cq.answer("Balansingiz yetarli emas.", show_alert=True)
        return
    await repo.add_balance(cq.from_user.id, -price)
    payment_id = await repo.create_payment(
        user_id=cq.from_user.id, ptype="CONTACT_UNLOCK", amount=price,
        order_id=order_id, status="APPROVED")
    unlock_id = await repo.create_unlock(order_id, cq.from_user.id, payment_id)
    await repo.update_unlock(unlock_id, approved_at=datetime.utcnow().isoformat(timespec="seconds"))
=======

    # contact_unlocks jadvalida CAS qiladigan status ustuni yo'q (order
    # o'zi PUBLISHED bo'lib qolaveradi), shuning uchun tugmani tez-tez
    # bosishdan himoya qilish uchun item bo'yicha asyncio.Lock ishlatamiz.
    lock_key = f"unlock:{order_id}:{cq.from_user.id}"
    async with get_lock(lock_key):
        already = await repo.get_approved_unlock(order_id, cq.from_user.id)
        pending = await repo.has_pending_unlock(order_id, cq.from_user.id)
        if already or pending:
            await state.clear()
            await cq.answer("Bu so'rov allaqachon amalga oshirilgan.", show_alert=True)
            return
        price = await repo.get_int_setting("contact_price", 25000)
        balance = await repo.get_balance(cq.from_user.id)
        if balance < price:
            await cq.answer("Balansingiz yetarli emas.", show_alert=True)
            return
        await repo.add_balance(cq.from_user.id, -price)
        payment_id = await repo.create_payment(
            user_id=cq.from_user.id, ptype="CONTACT_UNLOCK", amount=price,
            order_id=order_id, status="APPROVED")
        unlock_id = await repo.create_unlock(order_id, cq.from_user.id, payment_id)
        await repo.update_unlock(
            unlock_id, approved_at=datetime.utcnow().isoformat(timespec="seconds"))
    await maybe_notify_referral_bonus(cq.bot, cq.from_user.id)
>>>>>>> 963967d (Render deploy uchun tayyor)
    await state.clear()
    owner = await repo.get_user(order["user_id"])
    uname = f"@{owner['username']}" if owner and owner.get("username") else "—"
    await cq.answer("✅ To'landi!")
    await cq.message.edit_text(f"✅ To'lov muvaffaqiyatli!\n\n👤 Kontakt: {uname} "
                                f"(id: {order['user_id']})")


@router.callback_query(F.data == "unlock:pay_card")
async def unlock_pay_card(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("order_id"):
        await cq.answer("Zakaz topilmadi.", show_alert=True)
        return
    await state.set_state(UnlockStates.awaiting_receipt)
    await cq.answer()
    await cq.message.answer(
        "📎 Chekni yuboring\n\nTo'lovni amalga oshirgach, chek rasmini shu "
        "chatga yuboring.", reply_markup=kb.cancel_kb())


@router.message(UnlockStates.awaiting_receipt, F.photo)
async def unlock_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    code = data.get("public_code")
    order = await repo.get_order(order_id) if order_id else None
    if not order:
        await state.clear()
        await message.answer("Xatolik: zakaz topilmadi.")
        return

    receipt_file_id = message.photo[-1].file_id
    price = await repo.get_int_setting("contact_price", 25000)
    payment_id = await repo.create_payment(
        user_id=message.from_user.id, ptype="CONTACT_UNLOCK", amount=price,
        order_id=order_id, status="WAITING_ADMIN")
    await repo.update_payment(payment_id, receipt_file_id=receipt_file_id)
    await repo.create_unlock(order_id, message.from_user.id, payment_id)
    await state.clear()

    await message.answer("✅ Chekingiz qabul qilindi! Admin tasdiqlagach kontakt "
                          "ma'lumoti sizga yuboriladi.")
    for admin_id in await repo.list_admin_ids():
        try:
            await message.bot.send_photo(
                chat_id=admin_id, photo=receipt_file_id,
                caption=(f"📞 KONTAKT TO'LOVI\n\n"
                         f"👤 Developer: @{message.from_user.username or '—'} "
                         f"(id: {message.from_user.id})\n"
                         f"🆔 Zakaz: {code}\n💰 {price:,} so'm"),
                reply_markup=kb.receipt_admin_kb(payment_id))
        except Exception:
            logger.warning("Admin (%s) ga xabar yuborilmadi", admin_id)


@router.message(UnlockStates.awaiting_receipt)
async def unlock_receipt_wrong(message: Message):
    await message.answer("📎 Iltimos, to'lov chekini rasm ko'rinishida yuboring.",
                          reply_markup=kb.cancel_kb())
