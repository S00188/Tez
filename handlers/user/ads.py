import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database.repo as repo
import keyboards.keyboards as kb
from services.payment import offer_payment
from services.channel import publish_ad
from states import AdStates

logger = logging.getLogger(__name__)
router = Router(name="user_ads")


@router.message(F.text == kb.BTN_AD)
async def ad_begin(message: Message, state: FSMContext):
    user = await repo.get_or_create_user(message.from_user.id)
    active = await repo.count_user_active_ads(user["telegram_id"])
    max_active = await repo.get_int_setting("max_active_ads", 5)
    if active >= max_active:
        await message.answer(
            f"⛔️ Sizda faol e'lonlar soni limitga yetdi ({max_active} ta).\n"
            "Avval eskilaridan birini yakunlang yoki o'chiring.",
            reply_markup=kb.main_menu_rb(await repo.is_admin(message.from_user.id)))
        return
    await state.set_state(AdStates.awaiting_content)
    guide = await repo.get_setting("ad_guide") or "📢 E'lon berish"
    await message.answer(guide, reply_markup=kb.ad_guarantee_kb())


@router.callback_query(F.data == "ad:guarantee")
async def ad_guarantee(cq: CallbackQuery):
    text = await repo.get_setting("ad_guarantee") or "❓ Kafolat matni yo'q."
    await cq.answer()
    await cq.message.answer(text, reply_markup=kb.guarantee_info_kb())


@router.callback_query(F.data == "ok")
async def ok_dismiss(cq: CallbackQuery):
    await cq.answer()
    try:
        await cq.message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "cancel")
async def cancel_flow(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.answer("Bekor qilindi")
    is_admin = await repo.is_admin(cq.from_user.id)
    try:
        await cq.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cq.message.answer("❌ Bekor qilindi.", reply_markup=kb.main_menu_rb(is_admin))


async def _image_required() -> bool:
    return (await repo.get_setting("image_required", "1")) == "1"


@router.message(AdStates.awaiting_content, F.photo)
async def ad_content_photo(message: Message, state: FSMContext):
    caption = message.caption or ""
    user = await repo.get_or_create_user(message.from_user.id)
    ad_id, code = await repo.create_ad(
        user_id=user["telegram_id"], message_type="PHOTO",
        telegram_file_id=message.photo[-1].file_id,
        caption=caption, text=None, status="WAITING_PAYMENT")
    await state.update_data(kind="ad", item_id=ad_id, public_code=code)
    price = await repo.get_int_setting("ad_price", 34990)
    await message.answer(
        f"✅ E'loningiz qabul qilindi!\n\n"
        f"E'lon joylash narxi {price:,} so'm ni tashkil etadi.\n"
        f"Iltimos, to'lovni amalga oshiring.\n\n"
        f"🆔 Kod: {code}")
    await offer_payment(message, price, "ad")


@router.message(AdStates.awaiting_content, F.text)
async def ad_content_text(message: Message, state: FSMContext):
    if await _image_required():
        await message.answer(
            "⚠️ Rasm majburiy. Iltimos, rasm va matnni bitta xabarda yuboring.",
            reply_markup=kb.cancel_kb())
        return
    user = await repo.get_or_create_user(message.from_user.id)
    ad_id, code = await repo.create_ad(
        user_id=user["telegram_id"], message_type="TEXT",
        telegram_file_id=None, caption=None, text=message.text,
        status="WAITING_PAYMENT")
    await state.update_data(kind="ad", item_id=ad_id, public_code=code)
    price = await repo.get_int_setting("ad_price", 34990)
    await message.answer(
        f"✅ E'loningiz qabul qilindi!\n\n"
        f"E'lon joylash narxi {price:,} so'm ni tashkil etadi.\n"
        f"Iltimos, to'lovni amalga oshiring.\n\n"
        f"🆔 Kod: {code}")
    await offer_payment(message, price, "ad")


@router.callback_query(F.data == "ad:pay_balance")
async def ad_pay_balance(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ad_id = data.get("item_id")
    ad = await repo.get_ad(ad_id) if ad_id else None
    if not ad or ad["status"] != "WAITING_PAYMENT":
        await cq.answer("Bu e'lon topilmadi yoki allaqachon qayta ishlangan.",
                         show_alert=True)
        return
    price = await repo.get_int_setting("ad_price", 34990)
    balance = await repo.get_balance(cq.from_user.id)
    if balance < price:
        await cq.answer("Balansingiz yetarli emas.", show_alert=True)
        return
    await repo.add_balance(cq.from_user.id, -price)
    await repo.create_payment(user_id=cq.from_user.id, ptype="AD_PUBLICATION",
                               amount=price, ad_id=ad_id, status="APPROVED")
    msg_id = await publish_ad(cq.bot, await repo.get_ad(ad_id))
    await state.clear()
    await cq.answer("✅ To'landi!")
    if msg_id:
        await cq.message.edit_text(
            f"✅ E'loningiz tasdiqlandi!\n\n📢 E'loningiz kanalga joylashtirildi.\n\n"
            f"Rahmat! ❤️")
    else:
        await cq.message.edit_text(
            "✅ To'lov qabul qilindi, lekin kanalga joylashda texnik xatolik "
            "yuz berdi. Admin tez orada ko'rib chiqadi.")


@router.callback_query(F.data == "ad:pay_card")
async def ad_pay_card(cq: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ad_id = data.get("item_id")
    ad = await repo.get_ad(ad_id) if ad_id else None
    if not ad or ad["status"] != "WAITING_PAYMENT":
        await cq.answer("Bu e'lon topilmadi yoki allaqachon qayta ishlangan.",
                         show_alert=True)
        return
    await repo.update_ad(ad_id, status="WAITING_RECEIPT")
    await state.set_state(AdStates.awaiting_receipt)
    await cq.answer()
    await cq.message.answer(
        "📎 Chekni yuboring\n\n"
        "To'lovni amalga oshirgach, chek rasmini shu chatga yuboring.\n"
        "⚠️ Chekdagi summa ko'rinib turishi kerak.",
        reply_markup=kb.cancel_kb())


@router.message(AdStates.awaiting_receipt, F.photo)
async def ad_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    ad_id = data.get("item_id")
    code = data.get("public_code")
    ad = await repo.get_ad(ad_id) if ad_id else None
    if not ad:
        await state.clear()
        await message.answer("Xatolik: e'lon topilmadi. Qaytadan urinib ko'ring.",
                              reply_markup=kb.main_menu_rb(await repo.is_admin(message.from_user.id)))
        return

    receipt_file_id = message.photo[-1].file_id
    dup = await repo.find_approved_payment_by_receipt(receipt_file_id)

    price = await repo.get_int_setting("ad_price", 34990)
    payment_id = await repo.create_payment(
        user_id=message.from_user.id, ptype="AD_PUBLICATION", amount=price,
        ad_id=ad_id, status="WAITING_ADMIN")
    await repo.update_payment(payment_id, receipt_file_id=receipt_file_id)
    await repo.update_ad(ad_id, status="WAITING_ADMIN")
    await state.clear()

    await message.answer(
        f"✅ Chekingiz qabul qilindi!\n\n"
        f"To'lovingiz admin tomonidan tekshirilmoqda.\n"
        f"⏳ Tasdiqlangandan keyin e'loningiz kanalga joylashtiriladi.\n\n"
        f"🆔 E'lon raqamingiz: {code}\n\nIltimos, kuting.",
        reply_markup=kb.main_menu_rb(await repo.is_admin(message.from_user.id)))

    warn = ("\n\n⚠️ DIQQAT: bu chek rasmi ilgari tasdiqlangan boshqa to'lovda "
            "ham ishlatilgan bo'lishi mumkin!") if dup else ""
    for admin_id in await repo.list_admin_ids():
        try:
            await message.bot.send_photo(
                chat_id=admin_id, photo=receipt_file_id,
                caption=(
                    f"📢 YANGI E'LON\n\n"
                    f"👤 Foydalanuvchi: @{message.from_user.username or '—'}\n"
                    f"🆔 User ID: {message.from_user.id}\n\n"
                    f"🆔 E'lon: {code}\n"
                    f"💰 Summa: {price:,} so'm{warn}"),
                reply_markup=kb.receipt_admin_kb(payment_id))
        except Exception:
            logger.warning("Admin (%s) ga xabar yuborilmadi", admin_id)


@router.message(AdStates.awaiting_receipt)
async def ad_receipt_wrong(message: Message):
    await message.answer("📎 Iltimos, to'lov chekini rasm ko'rinishida yuboring.",
                          reply_markup=kb.cancel_kb())
