import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

<<<<<<< HEAD
import database.repo as repo
import keyboards.keyboards as kb
from services.channel import publish_ad, publish_order, delete_channel_post
=======
import config
import database.repo as repo
import keyboards.keyboards as kb
from services.channel import publish_ad, publish_order, delete_channel_post
from services.payment import maybe_notify_referral_bonus
>>>>>>> 963967d (Render deploy uchun tayyor)
from states import RejectStates, SettingsStates

logger = logging.getLogger(__name__)
router = Router(name="admin_panel")

SETTINGS_MENU = [
    ("ad_price", "💰 E'lon narxi"),
    ("order_price", "💰 Zakaz narxi"),
    ("contact_price", "💰 Kontakt narxi"),
    ("card_number", "💳 Karta raqami"),
    ("card_holder", "👤 Karta egasi"),
    ("referral_enabled", "🤝 Referal (1/0)"),
    ("referral_bonus", "🎁 Referal bonusi"),
    ("max_active_ads", "📢 Max faol e'lonlar"),
    ("max_active_orders", "🔵 Max faol zakazlar"),
    ("image_required", "📐 Rasm majburiymi (1/0)"),
    ("start_text", "📝 /start xabari"),
    ("ad_guide", "📝 E'lon yo'riqnomasi"),
    ("order_guide", "📝 Zakaz yo'riqnomasi"),
    ("ad_guarantee", "📝 E'lon kafolati matni"),
    ("order_guarantee", "📝 Zakaz kafolati matni"),
    ("rules_text", "📝 Qoidalar matni"),
]


async def _guard(cq_or_msg) -> bool:
    uid = cq_or_msg.from_user.id
    return await repo.is_admin(uid)


@router.message(Command("admin"))
@router.message(F.text == kb.BTN_ADMIN)
async def admin_cmd(message: Message, state: FSMContext):
    if not await _guard(message):
        await message.answer("⛔️ Sizda bu bo'limga huquq yo'q.")
        return
    await state.clear()
    await message.answer("🛠 Admin panel", reply_markup=kb.admin_sections_kb())


@router.callback_query(F.data == "admin:sections")
async def admin_sections(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    await cq.answer()
    await cq.message.edit_text("🛠 Admin panel", reply_markup=kb.admin_sections_kb())


# ============== KUTILAYOTGANLAR / CHEK MODERATSIYASI ==============
<<<<<<< HEAD
@router.callback_query(F.data == "admin:pending")
=======
@router.callback_query(F.data.regexp(r"^admin:pending(:next:(\d+))?$"))
>>>>>>> 963967d (Render deploy uchun tayyor)
async def admin_pending(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
<<<<<<< HEAD
    payments = await repo.list_payments_by_status("WAITING_ADMIN", limit=1)
    total = await repo.count_pending_payments()
    await cq.answer()
    if not payments:
        await cq.message.edit_text("✅ Hozircha kutilayotgan to'lov yo'q.",
                                    reply_markup=kb.back_to_admin_kb())
        return
    p = payments[0]
    target = f"🆔 AD: {p['ad_id']}" if p["ad_id"] else f"🆔 ORDER: {p['order_id']}"
    text = (f"⏳ Kutilayotgan to'lovlar: {total} ta\n\n"
            f"💳 To'lov #{p['id']} ({p['type']})\n"
            f"👤 user_id: {p['user_id']}\n💵 Summa: {p['amount']:,} so'm\n{target}")
    if p.get("receipt_file_id"):
        await cq.message.answer_photo(p["receipt_file_id"], caption=text,
                                       reply_markup=kb.receipt_admin_kb(p["id"]))
    else:
        await cq.message.answer(text, reply_markup=kb.receipt_admin_kb(p["id"]))
=======
    parts = cq.data.split(":")
    offset = int(parts[2]) if len(parts) > 2 else 0
    payments = await repo.list_payments_by_status("WAITING_ADMIN", limit=1, offset=offset)
    total = await repo.count_pending_payments()
    await cq.answer()
    if not payments:
        text = "✅ Hozircha kutilayotgan to'lov yo'q." if offset == 0 else \
            "✅ Boshqa kutilayotgan to'lov yo'q."
        await cq.message.edit_text(text, reply_markup=kb.back_to_admin_kb())
        return
    p = payments[0]
    target = f"🆔 AD: {p['ad_id']}" if p["ad_id"] else f"🆔 ORDER: {p['order_id']}"
    text = (f"⏳ Kutilayotgan to'lovlar: {total} ta ({offset + 1}-{offset + 1})\n\n"
            f"💳 To'lov #{p['id']} ({p['type']})\n"
            f"👤 user_id: {p['user_id']}\n💵 Summa: {p['amount']:,} so'm\n{target}")
    # Tasdiqlash/rad etish tugmalari BILAN BIRGA "Keyingisi" ham ko'rsatiladi
    approve_reject = [
        (f"pay:approve:{p['id']}", "✅ Tasdiqlash"),
        (f"pay:reject:{p['id']}", "❌ Rad etish"),
    ]
    nav = []
    if offset + 1 < total:
        nav.append((f"admin:pending:next:{offset + 1}", "➡️ Keyingisi"))
    nav.append(("admin:sections", "⬅️ Admin menyu"))
    markup = kb.ipb(approve_reject + nav, widths=(2, len(nav)))
    if p.get("receipt_file_id"):
        await cq.message.answer_photo(p["receipt_file_id"], caption=text,
                                       reply_markup=markup)
    else:
        await cq.message.answer(text, reply_markup=markup)
>>>>>>> 963967d (Render deploy uchun tayyor)


async def _notify_user(bot, telegram_id, text):
    try:
        await bot.send_message(telegram_id, text)
    except Exception:
        logger.warning("Foydalanuvchi (%s) ga xabar yuborilmadi", telegram_id)


@router.callback_query(F.data.startswith("pay:approve:"))
async def pay_approve(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    payment_id = int(cq.data.split(":")[2])
    payment = await repo.get_payment(payment_id)
    if not payment or payment["status"] != "WAITING_ADMIN":
        await cq.answer("Bu to'lov allaqachon qayta ishlangan.", show_alert=True)
        return

    from datetime import datetime
    now = datetime.utcnow().isoformat(timespec="seconds")
    await repo.update_payment(payment_id, status="APPROVED", approved_at=now,
                               approved_by=cq.from_user.id)
    await repo.log_admin_action(cq.from_user.id, "APPROVE_PAYMENT", "payment",
                                 str(payment_id))
<<<<<<< HEAD
=======
    await maybe_notify_referral_bonus(cq.bot, payment["user_id"])
>>>>>>> 963967d (Render deploy uchun tayyor)
    await cq.answer("✅ Tasdiqlandi")

    if payment["type"] == "AD_PUBLICATION" and payment["ad_id"]:
        ad = await repo.get_ad(payment["ad_id"])
        msg_id = await publish_ad(cq.bot, ad)
        if msg_id:
            await _notify_user(cq.bot, payment["user_id"],
                                "✅ E'loningiz tasdiqlandi!\n\n📢 E'loningiz kanalga "
                                "joylashtirildi.\n\nRahmat! ❤️")
        else:
            await _notify_user(cq.bot, payment["user_id"],
                                "✅ To'lovingiz tasdiqlandi, lekin kanalga joylashda "
                                "texnik xatolik yuz berdi. Admin bilan bog'laning.")
        await cq.message.edit_caption(caption="✅ TASDIQLANDI") if cq.message.caption \
            else await cq.message.edit_text("✅ TASDIQLANDI")

    elif payment["type"] == "ORDER_PUBLICATION" and payment["order_id"]:
        order = await repo.get_order(payment["order_id"])
        msg_id = await publish_order(cq.bot, order)
        if msg_id:
            await _notify_user(cq.bot, payment["user_id"],
                                "✅ Zakazingiz tasdiqlandi!\n\n📢 Zakazingiz kanalga "
                                "joylashtirildi.\n\nRahmat! ❤️")
        else:
            await _notify_user(cq.bot, payment["user_id"],
                                "✅ To'lovingiz tasdiqlandi, lekin kanalga joylashda "
                                "texnik xatolik yuz berdi. Admin bilan bog'laning.")
        await cq.message.edit_caption(caption="✅ TASDIQLANDI") if cq.message.caption \
            else await cq.message.edit_text("✅ TASDIQLANDI")

    elif payment["type"] == "CONTACT_UNLOCK" and payment["order_id"]:
        order = await repo.get_order(payment["order_id"])
        # shu to'lovga bog'liq unlock yozuvini topamiz
        from database.db import get_db
        conn = await get_db()
        cur = await conn.execute(
            "SELECT * FROM contact_unlocks WHERE payment_id = ? LIMIT 1",
            (payment_id,))
        row = await cur.fetchone()
        if row:
            unlock = dict(row)
            await repo.update_unlock(unlock["id"], approved_at=now)
            owner = await repo.get_user(order["user_id"]) if order else None
            uname = f"@{owner['username']}" if owner and owner.get("username") else "—"
            await _notify_user(
                cq.bot, unlock["developer_user_id"],
                f"✅ To'lovingiz tasdiqlandi!\n\n👤 Kontakt: {uname} "
                f"(id: {order['user_id'] if order else '—'})")
        await cq.message.edit_caption(caption="✅ TASDIQLANDI") if cq.message.caption \
            else await cq.message.edit_text("✅ TASDIQLANDI")


@router.callback_query(F.data.startswith("pay:reject:"))
async def pay_reject(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    payment_id = int(cq.data.split(":")[2])
    payment = await repo.get_payment(payment_id)
    if not payment or payment["status"] != "WAITING_ADMIN":
        await cq.answer("Bu to'lov allaqachon qayta ishlangan.", show_alert=True)
        return
    await state.set_state(RejectStates.awaiting_reason)
    await state.update_data(reject_payment_id=payment_id)
    await cq.answer()
    await cq.message.answer("❌ Rad etish sababini yozing:")


@router.message(RejectStates.awaiting_reason, F.text)
async def pay_reject_reason(message: Message, state: FSMContext):
    if not await repo.is_admin(message.from_user.id):
        return
    data = await state.get_data()
    payment_id = data.get("reject_payment_id")
    await state.clear()
    payment = await repo.get_payment(payment_id) if payment_id else None
    if not payment:
        await message.answer("Xatolik: to'lov topilmadi.")
        return

    await repo.update_payment(payment_id, status="REJECTED",
                               reject_reason=message.text,
                               approved_by=message.from_user.id)
    await repo.log_admin_action(message.from_user.id, "REJECT_PAYMENT", "payment",
                                 str(payment_id), message.text)
    await message.answer("❌ Rad etildi.", reply_markup=kb.admin_sections_kb())

    if payment["type"] == "AD_PUBLICATION" and payment["ad_id"]:
        await repo.update_ad(payment["ad_id"], status="REJECTED")
    elif payment["type"] == "ORDER_PUBLICATION" and payment["order_id"]:
        await repo.update_order(payment["order_id"], status="REJECTED")

    await _notify_user(
        message.bot, payment["user_id"],
        f"❌ To'lovingiz rad etildi.\n\nSabab: {message.text}")


<<<<<<< HEAD
# ============== E'LONLAR / ZAKAZLAR RO'YXATI (qisqa) ==============
@router.callback_query(F.data == "admin:ads")
=======
# ============== E'LONLAR / ZAKAZLAR RO'YXATI (sahifalangan) ==============
_ADMIN_LIST_PAGE = 10


def _admin_list_kb(kind, items, offset, total):
    section = "admin:ads" if kind == "ad" else "admin:orders"
    rows = [(f"admin:item:{kind}:{it['id']}:{offset}",
              f"{it['public_code']} — {kb.STATUS_LABELS.get(it['status'], it['status'])}")
             for it in items]
    nav = []
    if offset > 0:
        nav.append((f"{section}:{max(0, offset - _ADMIN_LIST_PAGE)}", "⬅️ Oldingi"))
    if offset + _ADMIN_LIST_PAGE < total:
        nav.append((f"{section}:{offset + _ADMIN_LIST_PAGE}", "➡️ Keyingi"))
    markup_rows = rows + nav + [("admin:sections", "⬅️ Admin menyu")]
    widths = (1,) * len(rows) + ((len(nav),) if nav else ()) + (1,)
    return kb.ipb(markup_rows, widths=widths)


@router.callback_query(F.data.regexp(r"^admin:ads(:(\d+))?$"))
>>>>>>> 963967d (Render deploy uchun tayyor)
async def admin_ads(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
<<<<<<< HEAD
    from database.db import get_db
    conn = await get_db()
    cur = await conn.execute(
        "SELECT public_code, status FROM ads WHERE deleted_at IS NULL "
        "ORDER BY id DESC LIMIT 20")
    rows = await cur.fetchall()
    await cq.answer()
    if not rows:
        text = "📢 E'lonlar yo'q."
    else:
        lines = [f"{r['public_code']} — {kb.STATUS_LABELS.get(r['status'], r['status'])}"
                 for r in rows]
        text = "📢 So'nggi e'lonlar:\n\n" + "\n".join(lines)
    await cq.message.edit_text(text, reply_markup=kb.back_to_admin_kb())


@router.callback_query(F.data == "admin:orders")
=======
    parts = cq.data.split(":")
    offset = int(parts[2]) if len(parts) > 2 else 0
    items = await repo.list_ads_admin(limit=_ADMIN_LIST_PAGE, offset=offset)
    total = await repo.count_ads_admin()
    await cq.answer()
    text = f"📢 E'lonlar (jami {total} ta) — tanlang:" if items else "📢 E'lonlar yo'q."
    await cq.message.edit_text(text, reply_markup=_admin_list_kb("ad", items, offset, total))


@router.callback_query(F.data.regexp(r"^admin:orders(:(\d+))?$"))
>>>>>>> 963967d (Render deploy uchun tayyor)
async def admin_orders(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
<<<<<<< HEAD
    from database.db import get_db
    conn = await get_db()
    cur = await conn.execute(
        "SELECT public_code, status FROM orders WHERE deleted_at IS NULL "
        "ORDER BY id DESC LIMIT 20")
    rows = await cur.fetchall()
    await cq.answer()
    if not rows:
        text = "🔵 Zakazlar yo'q."
    else:
        lines = [f"{r['public_code']} — {kb.STATUS_LABELS.get(r['status'], r['status'])}"
                 for r in rows]
        text = "🔵 So'nggi zakazlar:\n\n" + "\n".join(lines)
    await cq.message.edit_text(text, reply_markup=kb.back_to_admin_kb())
=======
    parts = cq.data.split(":")
    offset = int(parts[2]) if len(parts) > 2 else 0
    items = await repo.list_orders_admin(limit=_ADMIN_LIST_PAGE, offset=offset)
    total = await repo.count_orders_admin()
    await cq.answer()
    text = f"🔵 Zakazlar (jami {total} ta) — tanlang:" if items else "🔵 Zakazlar yo'q."
    await cq.message.edit_text(text, reply_markup=_admin_list_kb("order", items, offset, total))


@router.callback_query(F.data.regexp(r"^admin:item:(ad|order):(\d+):(\d+)$"))
async def admin_item_detail(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    _, _, kind, item_id, offset = cq.data.split(":")
    item_id, offset = int(item_id), int(offset)
    item = await repo.get_ad(item_id) if kind == "ad" else await repo.get_order(item_id)
    await cq.answer()
    if not item:
        await cq.message.edit_text("Topilmadi.", reply_markup=kb.back_to_admin_kb())
        return
    label = kb.STATUS_LABELS.get(item["status"], item["status"])
    body = item.get("caption") or item.get("text") or ""
    text = (f"🆔 {item['public_code']}\n📌 Holat: {label}\n👤 user_id: {item['user_id']}"
            f"\n\n{body}")
    await cq.message.edit_text(text, reply_markup=kb.admin_item_detail_kb(kind, item_id, offset))


@router.callback_query(F.data.regexp(r"^admin:item_delete:(ad|order):(\d+):(\d+)$"))
async def admin_item_delete(cq: CallbackQuery):
    """Admin panelidan istalgan holatdagi e'lon/zakazni to'g'ridan-to'g'ri
    o'chirish — avval bu imkoniyat umuman yo'q edi, faqat foydalanuvchining
    o'zi (va faqat PUBLISHED holatda) o'chira olardi."""
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    _, _, kind, item_id, offset = cq.data.split(":")
    item_id, offset = int(item_id), int(offset)
    item = await repo.get_ad(item_id) if kind == "ad" else await repo.get_order(item_id)
    if not item:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    if item.get("channel_message_id"):
        await delete_channel_post(cq.bot, item["channel_message_id"])
    if kind == "ad":
        await repo.soft_delete_ad(item_id)
    else:
        await repo.soft_delete_order(item_id)
    await repo.log_admin_action(cq.from_user.id, "ADMIN_DELETE_ITEM", kind, str(item_id))
    await cq.answer("🗑 O'chirildi")
    items = (await repo.list_ads_admin(limit=_ADMIN_LIST_PAGE, offset=offset) if kind == "ad"
             else await repo.list_orders_admin(limit=_ADMIN_LIST_PAGE, offset=offset))
    total = (await repo.count_ads_admin() if kind == "ad" else await repo.count_orders_admin())
    label = "E'lonlar" if kind == "ad" else "Zakazlar"
    text = f"🗑 O'chirildi.\n\n{'📢' if kind == 'ad' else '🔵'} {label} (jami {total} ta):"
    await cq.message.edit_text(text, reply_markup=_admin_list_kb(kind, items, offset, total))
>>>>>>> 963967d (Render deploy uchun tayyor)


@router.callback_query(F.data == "admin:users")
async def admin_users(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    total = await repo.count_users()
    await cq.answer()
    await cq.message.edit_text(f"👥 Jami foydalanuvchilar: {total} ta.\n\n"
                                f"Qidirish uchun: /finduser <id yoki username>",
                                reply_markup=kb.back_to_admin_kb())


@router.message(Command("finduser"))
async def find_user(message: Message):
    if not await repo.is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /finduser <id yoki username>")
        return
    users = await repo.search_users(parts[1].strip())
    if not users:
        await message.answer("Hech kim topilmadi.")
        return
    lines = [f"{u['telegram_id']} — @{u['username'] or '—'} — "
             f"balans: {u['balance']:,} so'm" for u in users]
    await message.answer("\n".join(lines))


@router.callback_query(F.data == "admin:stats")
async def admin_stats(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    s = await repo.get_general_stats()
    await cq.answer()
    text = (
        "📊 Statistika\n\n"
        f"👥 Foydalanuvchilar: {s['users']}\n"
        f"📢 E'lonlar: {s['ads']} (kanalda: {s['ads_published']})\n"
        f"🔵 Zakazlar: {s['orders']} (kanalda: {s['orders_published']})\n"
        f"⚠️ Ochiq shikoyatlar: {s['complaints_open']}\n"
        f"💰 Jami tushum: {s['total_revenue']:,} so'm")
    await cq.message.edit_text(text, reply_markup=kb.back_to_admin_kb())


# ============== SOZLAMALAR ==============
@router.callback_query(F.data == "admin:settings")
async def admin_settings(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    await cq.answer()
    await cq.message.edit_text("⚙️ Sozlamalar — o'zgartirmoqchi bo'lgan "
                                "parametrni tanlang:",
                                reply_markup=kb.settings_list_kb(SETTINGS_MENU))


@router.callback_query(F.data.startswith("admin:setkey:"))
async def admin_setkey(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    key = cq.data.split(":", 2)[2]
    current = await repo.get_setting(key, "—")
    await state.set_state(SettingsStates.awaiting_value)
    await state.update_data(setting_key=key)
    await cq.answer()
    await cq.message.edit_text(
        f"⚙️ {key}\n\nHozirgi qiymat:\n{current}\n\nYangi qiymatni yuboring:")


<<<<<<< HEAD
=======
# ============== ADMINLAR RO'YXATI ==============
@router.callback_query(F.data == "admin:admins")
async def admin_admins(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    ids = await repo.list_admin_ids()
    env_ids = set(config.ADMIN_IDS)
    lines = [f"• {i}" + (" (.env, o'chirib bo'lmaydi)" if i in env_ids else "")
             for i in ids]
    await cq.answer()
    await cq.message.edit_text(
        "👤 Adminlar:\n\n" + ("\n".join(lines) if lines else "— yo'q —"),
        reply_markup=kb.admins_menu_kb())


@router.callback_query(F.data == "admin:add_admin")
async def admin_add_admin_start(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    await state.set_state(SettingsStates.awaiting_admin_id)
    await state.update_data(admin_action="add")
    await cq.answer()
    await cq.message.edit_text(
        "➕ Yangi admin qilib tayinlamoqchi bo'lgan foydalanuvchining "
        "Telegram ID raqamini yuboring:", reply_markup=kb.cancel_kb())


@router.callback_query(F.data == "admin:remove_admin")
async def admin_remove_admin_start(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    await state.set_state(SettingsStates.awaiting_admin_id)
    await state.update_data(admin_action="remove")
    await cq.answer()
    await cq.message.edit_text(
        "➖ Adminlikdan olib tashlamoqchi bo'lgan foydalanuvchining "
        "Telegram ID raqamini yuboring:", reply_markup=kb.cancel_kb())


@router.message(SettingsStates.awaiting_admin_id, F.text)
async def admin_set_admin_id(message: Message, state: FSMContext):
    if not await repo.is_admin(message.from_user.id):
        return
    data = await state.get_data()
    action = data.get("admin_action")
    await state.clear()
    raw = message.text.strip()
    if not raw.lstrip("-").isdigit():
        await message.answer("⚠️ Noto'g'ri format. Faqat raqam (Telegram ID) yuboring.",
                              reply_markup=kb.admin_sections_kb())
        return
    target_id = int(raw)

    if action == "add":
        await repo.add_admin(target_id, added_by=message.from_user.id)
        await repo.log_admin_action(message.from_user.id, "ADD_ADMIN", "user",
                                     str(target_id))
        await message.answer(f"✅ {target_id} admin qilib tayinlandi.",
                              reply_markup=kb.admin_sections_kb())
    elif action == "remove":
        ok = await repo.remove_admin(target_id, removed_by=message.from_user.id)
        if ok:
            await repo.log_admin_action(message.from_user.id, "REMOVE_ADMIN", "user",
                                         str(target_id))
            await message.answer(f"✅ {target_id} adminlikdan olib tashlandi.",
                                  reply_markup=kb.admin_sections_kb())
        else:
            await message.answer(
                "⛔️ Bu foydalanuvchi .env orqali admin qilingan — bazadan "
                "olib tashlab bo'lmaydi.", reply_markup=kb.admin_sections_kb())
    else:
        await message.answer("Xatolik yuz berdi.", reply_markup=kb.admin_sections_kb())


>>>>>>> 963967d (Render deploy uchun tayyor)
@router.message(SettingsStates.awaiting_value, F.text)
async def admin_set_value(message: Message, state: FSMContext):
    if not await repo.is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data.get("setting_key")
    await state.clear()
    if not key:
        return
    await repo.set_setting(key, message.text, message.from_user.id)
    await repo.log_admin_action(message.from_user.id, "SET_SETTING", "settings", key,
                                 message.text[:200])
    await message.answer(f"✅ '{key}' yangilandi.", reply_markup=kb.admin_sections_kb())
