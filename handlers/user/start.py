import logging

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database.repo as repo
import keyboards.keyboards as kb
from services.codes import decode_referral

logger = logging.getLogger(__name__)
router = Router(name="user_start")


async def _greet(message: Message, user_id_for_admin_check: int):
    is_admin = await repo.is_admin(user_id_for_admin_check)
    text = await repo.get_setting("start_text") or "🚀 Tezda Sotdim"
    await message.answer(text, reply_markup=kb.main_menu_rb(is_admin=is_admin))


@router.message(CommandStart(deep_link=True))
async def on_start_deep(message: Message):
    payload = message.text.split(maxsplit=1)[-1]
    ref_id = decode_referral(payload)

    existing = await repo.get_user(message.from_user.id)
    is_new = existing is None

    if ref_id == message.from_user.id:
        ref_id = None  # o'zini o'zi taklif qilolmaydi

    user = await repo.get_or_create_user(
        message.from_user.id, message.from_user.username,
        message.from_user.first_name, message.from_user.last_name,
        referred_by=ref_id if is_new else None)

    await repo.update_user(message.from_user.id,
                            username=message.from_user.username,
                            first_name=message.from_user.first_name,
                            last_name=message.from_user.last_name)

    await _greet(message, message.from_user.id)

    if is_new and ref_id:
        referrer = await repo.get_user(ref_id)
        referral_on = (await repo.get_setting("referral_enabled", "1")) == "1"
        if referrer and referral_on:
            bonus = await repo.get_int_setting("referral_bonus", 5000)
            await repo.add_balance(ref_id, bonus)
            await repo.log_admin_action(
                None, "REFERRAL_BONUS", "user", str(ref_id),
                f"+{bonus} so'm, taklif qilingan: {message.from_user.id}")
            try:
                await message.bot.send_message(
                    ref_id,
                    f"🤝 Siz orqali botga yangi foydalanuvchi qo'shildi!\n"
                    f"🎁 Balansingizga {bonus:,} so'm qo'shildi.")
            except Exception:
                logger.warning("Referal bonus xabari yuborilmadi: %s", ref_id)


@router.message(CommandStart())
async def on_start(message: Message):
    if message.from_user is None:
        return
    await repo.get_or_create_user(
        message.from_user.id, message.from_user.username,
        message.from_user.first_name, message.from_user.last_name)
    await _greet(message, message.from_user.id)


@router.message(Command("menu"))
@router.message(F.text == kb.BTN_HOME)
async def on_menu(message: Message):
    is_admin = await repo.is_admin(message.from_user.id)
    await message.answer("🏠 Bosh menyu", reply_markup=kb.main_menu_rb(is_admin=is_admin))


@router.message(F.text == kb.BTN_RULES)
async def on_rules(message: Message):
    text = await repo.get_setting("rules_text") or "ℹ️ Qoidalar hozircha kiritilmagan."
    await message.answer(text)


@router.message(Command("cancel"))
@router.message(F.text == kb.BTN_CANCEL)
async def on_cancel(message: Message, state: FSMContext):
    await state.clear()
    is_admin = await repo.is_admin(message.from_user.id)
    await message.answer("❌ Bekor qilindi.", reply_markup=kb.main_menu_rb(is_admin=is_admin))
