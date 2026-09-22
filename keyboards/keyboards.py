from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def reply_row(*labels):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=l) for l in labels]],
        resize_keyboard=True)


def multi_reply(rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=l) for l in r] for r in rows],
        resize_keyboard=True)


def ipb(items, widths=(1,)):
    """items: har biri (callback_data, matn) juftligi bo'lgan ro'yxat."""
    b = InlineKeyboardBuilder()
    for row in items:
        cb, text = row
        b.button(text=text, callback_data=cb)
    return b.adjust(*widths).as_markup()


# ================= ASOSIY MENYU (barcha foydalanuvchilar) =================
BTN_AD = "📢 E'lon berish"
BTN_ORDER = "🔵 Dasturga zakaz berish"
BTN_MY_ADS = "📋 Mening e'lonlarim"
BTN_MY_ORDERS = "📋 Mening zakazlarim"
BTN_REFERRAL = "🤝 Do'stlarni taklif qilish"
BTN_RULES = "ℹ️ Qoidalar"
BTN_ADMIN = "🛠 Admin panel"
BTN_CANCEL = "❌ Bekor qilish"
BTN_HOME = "🏠 Bosh menyu"


def main_menu_rb(is_admin: bool = False):
    rows = [
        [BTN_AD, BTN_ORDER],
        [BTN_MY_ADS, BTN_MY_ORDERS],
        [BTN_REFERRAL, BTN_RULES],
    ]
    if is_admin:
        rows.append([BTN_ADMIN])
    return multi_reply(rows)


def cancel_reply_kb():
    return reply_row(BTN_CANCEL)


def admin_menu_rb():
    return multi_reply([["🛠 Admin panel"], [BTN_HOME]])


def cancel_kb():
    return ipb([("cancel", "❌ Bekor qilish")])


# -================= AD (e'lon) oqimi =================
def ad_guarantee_kb():
    return ipb([("ad:guarantee", "❓ Botim sotilishiga kafolat bormi?"),
                ("cancel", "❌ Bekor qilish")])


def order_guarantee_kb():
    return ipb([("order:guarantee", "❓ Zakaz bajarilishiga kafolat bormi?"),
                ("cancel", "❌ Bekor qilish")])


def guarantee_info_kb():
    return ipb([("ok", "👌 Tushunarli")])


def payment_choice_kb(prefix: str):
    """prefix: 'ad' | 'order' | 'unlock' — balans yetarli bo'lganda."""
    return ipb([
        (f"{prefix}:pay_balance", "💰 Balansdan to'lash"),
        (f"{prefix}:pay_card", "💳 Karta orqali"),
        ("cancel", "❌ Bekor qilish"),
    ], widths=(1, 1, 1))


def pay_card_only_kb():
    return ipb([("cancel", "❌ Bekor qilish")])


# ================= ADMIN: to'lov moderatsiyasi =================
def receipt_admin_kb(payment_id):
    return ipb([
        (f"pay:approve:{payment_id}", "✅ Tasdiqlash"),
        (f"pay:reject:{payment_id}", "❌ Rad etish"),
    ], widths=(2,))


# ================= Mening e'lonlarim / zakazlarim =================
def items_list_kb(items, kind: str):
    """kind: 'ad' | 'order' — ro'yxatdagi har bir element uchun tugma."""
    rows = []
    for it in items:
        title = f"{it['public_code']} — {STATUS_LABELS.get(it['status'], it['status'])}"
        rows.append((f"{kind}:view:{it['id']}", title))
    if not rows:
        return None
    return ipb(rows, widths=(1,))


<<<<<<< HEAD
def item_detail_kb(kind: str, item_id: int, can_complete: bool):
    rows = [(f"{kind}:back_list", "⬅️ Ro'yxatga")]
    if can_complete:
        rows.insert(0, (f"{kind}:complete:{item_id}", "✅ Bajarildi deb belgilash"))
        rows.insert(1, (f"{kind}:delete:{item_id}", "🗑 O'chirish"))
=======
def item_detail_kb(kind: str, item_id: int, status: str):
    """Har qanday holatdagi (faqat allaqachon o'chirilgan bo'lmasa) e'lon/
    zakaz uchun "O'chirish" tugmasini ko'rsatadi — avval faqat PUBLISHED
    holatida ko'rinar edi, shu sabab bekor qilingan/rad etilgan/to'lov
    kutayotgan yozuvlarni foydalanuvchi o'zi hech qachon o'chira olmas,
    kvotasi abadiy band bo'lib qolar edi. "Bajarildi" tugmasi esa faqat
    kanalda joylashtirilgan (PUBLISHED) elementlar uchun mantiqan to'g'ri."""
    rows = [(f"{kind}:back_list", "⬅️ Ro'yxatga")]
    if status == "PUBLISHED":
        rows.insert(0, (f"{kind}:complete:{item_id}", "✅ Bajarildi deb belgilash"))
    if status != "DELETED":
        rows.insert(0, (f"{kind}:delete:{item_id}", "🗑 O'chirish"))
>>>>>>> 963967d (Render deploy uchun tayyor)
    return ipb(rows, widths=(1,))


STATUS_LABELS = {
    "DRAFT": "qoralama",
    "WAITING_PAYMENT": "to'lov kutilmoqda",
    "WAITING_RECEIPT": "chek kutilmoqda",
    "WAITING_ADMIN": "admin tasdig'i kutilmoqda",
<<<<<<< HEAD
=======
    "PROCESSING": "to'lov qayta ishlanmoqda",
>>>>>>> 963967d (Render deploy uchun tayyor)
    "APPROVED": "tasdiqlangan",
    "PUBLISHED": "kanalda e'lon qilingan",
    "REJECTED": "rad etilgan",
    "COMPLETED": "bajarilgan",
    "CANCELLED": "bekor qilingan",
    "DELETED": "o'chirilgan",
}


# ================= Kanal posti tugmalari =================
def order_channel_kb(public_code):
    return ipb([
        (f"order:apply:{public_code}", "📩 Men buni qila olaman"),
        (f"complaint:start:{public_code}", "⚠️ Shikoyat qilish"),
    ], widths=(1, 1))


def ad_channel_kb(public_code):
    return ipb([
        (f"complaint:start:{public_code}", "⚠️ Shikoyat qilish"),
    ])


def developer_order_kb(public_code, already_unlocked: bool):
    if already_unlocked:
        return ipb([("cancel", "⬅️ Orqaga")])
    return ipb([
        (f"unlock:start:{public_code}", "📞 Kontaktni olish"),
        ("cancel", "⬅️ Orqaga"),
    ], widths=(1, 1))


# ================= Shikoyat (admin) =================
def complaint_admin_kb(complaint_id):
    return ipb([
        (f"complaint:delete_post:{complaint_id}", "🗑 Postni o'chirish"),
        (f"complaint:block_user:{complaint_id}", "🚫 Userni bloklash"),
        (f"complaint:dismiss:{complaint_id}", "✅ E'tiborsiz qoldirish"),
    ], widths=(1, 1, 1))


# ================= Broadcast =================
def broadcast_kb():
    return ipb([
        ("bcast:confirm", "✅ Yuborish"),
        ("bcast:cancel", "❌ Bekor"),
    ], widths=(2,))


# ================= Admin panel bosh menyusi =================
def admin_sections_kb():
    return ipb([
        ("admin:pending", "⏳ Kutilayotganlar"),
        ("admin:ads", "📢 E'lonlar"),
        ("admin:orders", "🔵 Zakazlar"),
        ("admin:users", "👥 Foydalanuvchilar"),
        ("admin:complaints", "⚠️ Shikoyatlar"),
        ("admin:stats", "📊 Statistika"),
        ("admin:settings", "⚙️ Sozlamalar"),
        ("admin:sign", "✍️ Kanal imzosi"),
        ("admin:broadcast", "📣 Reklama yuborish"),
<<<<<<< HEAD
    ], widths=(2, 2, 2, 2, 1))
=======
        ("admin:admins", "👤 Adminlar"),
    ], widths=(2, 2, 2, 2, 1, 1))


def admins_menu_kb():
    return ipb([
        ("admin:add_admin", "➕ Admin qo'shish"),
        ("admin:remove_admin", "➖ Admin olib tashlash"),
        ("admin:sections", "⬅️ Orqaga"),
    ], widths=(1, 1, 1))


def pending_pagination_kb(offset, total, per_page=1):
    """Kutilayotgan to'lovlar/shikoyatlar ro'yxatida "Keyingisi" tugmasi."""
    rows = []
    if offset + per_page < total:
        rows.append((f"admin:pending:next:{offset + per_page}", "➡️ Keyingisi"))
    rows.append(("admin:sections", "⬅️ Admin menyu"))
    return ipb(rows, widths=(1,))


def complaints_pagination_kb(offset, total, complaint_id, per_page=1):
    rows = [
        (f"complaint:delete_post:{complaint_id}", "🗑 Postni o'chirish"),
        (f"complaint:block_user:{complaint_id}", "🚫 Userni bloklash"),
        (f"complaint:dismiss:{complaint_id}", "✅ E'tiborsiz qoldirish"),
    ]
    if offset + per_page < total:
        rows.append((f"admin:complaints:next:{offset + per_page}", "➡️ Keyingisi"))
    rows.append(("admin:sections", "⬅️ Admin menyu"))
    return ipb(rows, widths=(1, 1, 1, 1))


def admin_item_detail_kb(kind: str, item_id: int, page_offset: int = 0):
    """Admin panelidagi ro'yxatdagi bitta e'lon/zakazni o'chirish imkoni
    (avval admin panelida individual item'ni o'chirish imkoniyati umuman
    yo'q edi)."""
    section = "admin:ads" if kind == "ad" else "admin:orders"
    return ipb([
        (f"admin:item_delete:{kind}:{item_id}:{page_offset}", "🗑 O'chirish"),
        (f"{section}:{page_offset}", "⬅️ Ro'yxatga"),
    ], widths=(1, 1))
>>>>>>> 963967d (Render deploy uchun tayyor)


def settings_list_kb(keys_labels):
    rows = [(f"admin:setkey:{k}", label) for k, label in keys_labels]
    rows.append(("admin:sections", "⬅️ Orqaga"))
    return ipb(rows, widths=(1,))


def back_to_admin_kb():
    return ipb([("admin:sections", "⬅️ Admin menyu")])
