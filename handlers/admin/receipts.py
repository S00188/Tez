"""⚠️ Shikoyatlarni admin tomonidan ko'rib chiqish (post o'chirish / userni
bloklash / e'tiborsiz qoldirish)."""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

import database.repo as repo
import keyboards.keyboards as kb
from services.channel import delete_channel_post

logger = logging.getLogger(__name__)
router = Router(name="admin_receipts")


async def _guard(cq) -> bool:
    return await repo.is_admin(cq.from_user.id)


async def _find_by_code(code):
    ad = await repo.get_ad_by_code(code)
    if ad:
        return "ad", ad
    order = await repo.get_order_by_code(code)
    if order:
        return "order", order
    return None, None


@router.callback_query(F.data == "admin:complaints")
async def admin_complaints(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    complaints = await repo.list_complaints("OPEN", limit=1)
    total = await repo.count_complaints("OPEN")
    await cq.answer()
    if not complaints:
        await cq.message.edit_text("✅ Ochiq shikoyatlar yo'q.",
                                    reply_markup=kb.back_to_admin_kb())
        return
    c = complaints[0]
    await cq.message.edit_text(
        f"⚠️ Ochiq shikoyatlar: {total} ta\n\n"
        f"🆔 {c['target_code']}\nSabab: {c['reason']}\n"
        f"Shikoyatchi: {c['user_id']}",
        reply_markup=kb.complaint_admin_kb(c["id"]))


@router.callback_query(F.data.startswith("complaint:delete_post:"))
async def complaint_delete_post(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    complaint_id = int(cq.data.split(":")[2])
    complaint = await repo.get_complaint(complaint_id)
    await cq.answer()
    if not complaint:
        await cq.message.edit_text("Topilmadi.")
        return
    kind, item = await _find_by_code(complaint["target_code"])
    if item and item.get("channel_message_id"):
        await delete_channel_post(cq.bot, item["channel_message_id"])
        if kind == "ad":
            await repo.update_ad(item["id"], status="REJECTED")
        else:
            await repo.update_order(item["id"], status="REJECTED")
    await repo.update_complaint(complaint_id, status="RESOLVED")
    await repo.log_admin_action(cq.from_user.id, "COMPLAINT_DELETE_POST",
                                 "complaint", str(complaint_id))
    await cq.message.edit_text(f"🗑 {complaint['target_code']} posti o'chirildi.")


@router.callback_query(F.data.startswith("complaint:block_user:"))
async def complaint_block_user(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    complaint_id = int(cq.data.split(":")[2])
    complaint = await repo.get_complaint(complaint_id)
    await cq.answer()
    if not complaint:
        await cq.message.edit_text("Topilmadi.")
        return
    kind, item = await _find_by_code(complaint["target_code"])
    if item:
        await repo.set_blocked(item["user_id"], True)
        await repo.update_complaint(complaint_id, status="RESOLVED")
        await repo.log_admin_action(cq.from_user.id, "COMPLAINT_BLOCK_USER",
                                     "complaint", str(complaint_id))
        await cq.message.edit_text(
            f"🚫 Foydalanuvchi (id: {item['user_id']}) bloklandi.")
    else:
        await cq.message.edit_text("Nishon egasi topilmadi.")


@router.callback_query(F.data.startswith("complaint:dismiss:"))
async def complaint_dismiss(cq: CallbackQuery):
    if not await _guard(cq):
        await cq.answer("⛔️", show_alert=True)
        return
    complaint_id = int(cq.data.split(":")[2])
    await repo.update_complaint(complaint_id, status="DISMISSED")
    await cq.answer("✅")
    await cq.message.edit_text("✅ Shikoyat e'tiborsiz qoldirildi.")
