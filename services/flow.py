"""E'lon/zakaz/kontakt-unlock oqimlarini boshqarish uchun umumiy yordamchi.

MUHIM: foydalanuvchi to'lovni ko'rib bekor qilsa, boshqa menyu tugmasini
bossa yoki umuman javob bermay ketsa ham, ad_content_photo/text bosqichida
DB'da yaratilgan WAITING_PAYMENT (yoki WAITING_RECEIPT) yozuv hech qachon
o'chmasdan "faol" bo'lib qolib, foydalanuvchining e'lon/zakaz kvotasini
abadiy band qilib qo'yishi mumkin edi. Har qanday joyda joriy FSM oqimidan
chiqishdan oldin shu funksiya chaqirilishi kerak — u yarim qolgan yozuvni
CANCELLED qilib belgilaydi va keyin state'ni tozalaydi.
"""
import logging

from aiogram.fsm.context import FSMContext

import database.repo as repo

logger = logging.getLogger(__name__)

_CANCELLABLE_STATUSES = ("WAITING_PAYMENT", "WAITING_RECEIPT")


async def abandon_pending_flow(state: FSMContext):
    """Joriy FSM state'da boshlangan, lekin hali to'lanmagan/tasdiqlanmagan
    e'lon yoki zakaz bo'lsa — uni CANCELLED qilib belgilaydi, so'ng FSM
    state'ni butunlay tozalaydi. Turli oqimlarga tegishli kalitlar bir xil
    FSM state ustida saqlanganligi sababli (kind/item_id/order_id), boshqa
    oqimga o'tishdan oldin har doim shu orqali "yakunlash" kerak — aks
    holda eski oqim ma'lumotlari qisman qolib ketishi mumkin."""
    data = await state.get_data()
    kind = data.get("kind")
    try:
        if kind == "ad":
            ad_id = data.get("item_id")
            if ad_id:
                ad = await repo.get_ad(ad_id)
                if ad and ad["status"] in _CANCELLABLE_STATUSES:
                    await repo.update_ad(ad_id, status="CANCELLED")
        elif kind == "order":
            order_id = data.get("item_id")
            if order_id:
                order = await repo.get_order(order_id)
                if order and order["status"] in _CANCELLABLE_STATUSES:
                    await repo.update_order(order_id, status="CANCELLED")
        # kind == "unlock" uchun alohida yozuv faqat to'lov
        # (pay_balance/pay_card) bosilganda yaratiladi — offer_payment
        # bosqichida hali DB yozuvi yo'q, shuning uchun tozalash shart emas.
    except Exception:
        logger.exception("Yarim qolgan oqimni bekor qilishda xato (kind=%s)", kind)
    await state.clear()
