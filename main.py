import asyncio
import logging

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, TelegramObject

import config
import database.repo as repo
from database.db import init_db, close_db

logging.basicConfig(level=logging.INFO,
                     format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class BlockedUserMiddleware(BaseMiddleware):
    """Admin tomonidan bloklangan foydalanuvchilarni botdan foydalanishdan
    to'xtatadi."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user is not None:
            if await repo.is_user_blocked(user.id):
                return None
        return await handler(event, data)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(BlockedUserMiddleware())
    dp.callback_query.middleware(BlockedUserMiddleware())

    from handlers.user import start, ads, orders, mine, referral, complaint
    from handlers.admin import panel, broadcast, receipts, sign

    # Foydalanuvchi routerlari
    dp.include_router(start.router)
    dp.include_router(ads.router)
    dp.include_router(orders.router)
    dp.include_router(mine.router)
    dp.include_router(referral.router)
    dp.include_router(complaint.router)

    # Admin routerlari
    dp.include_router(panel.router)
    dp.include_router(receipts.router)
    dp.include_router(sign.router)
    dp.include_router(broadcast.router)

    return dp


async def on_startup(bot: Bot):
    await init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Bosh menyu"),
        BotCommand(command="menu", description="🏠 Bosh menyu"),
        BotCommand(command="cancel", description="❌ Bekor qilish"),
        BotCommand(command="admin", description="🛠 Admin panel"),
    ], scope=BotCommandScopeDefault())

    if config.RUN_MODE == "webhook":
        if not config.WEBHOOK_URL:
            raise SystemExit(
                "RUN_MODE=webhook, lekin WEBHOOK_HOST .env'da ko'rsatilmagan!")
        await bot.set_webhook(
            url=config.WEBHOOK_URL,
            secret_token=config.WEBHOOK_SECRET or None,
            drop_pending_updates=True)
        logger.info("Webhook o'rnatildi: %s", config.WEBHOOK_URL)
    else:
        await bot.delete_webhook(drop_pending_updates=True)

    for admin_id in await repo.list_admin_ids():
        try:
            await bot.send_message(admin_id, "✅ Bot ishga tushdi! Admin panel: /admin")
        except Exception as exc:
            logger.warning("Admin %s'ga xabar yuborilmadi: %s", admin_id, exc)


async def on_shutdown(bot: Bot):
    await close_db()


def build_bot() -> Bot:
    return Bot(token=config.BOT_TOKEN)


# ============================================================
#  POLLING — lokal ishlab chiqish uchun (RUN_MODE=polling, standart)
# ============================================================
async def run_polling():
    bot = build_bot()
    dp = build_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


# ============================================================
#  WEBHOOK — Render (va boshqa bepul/HTTP-asoslangan hostinglar) uchun.
#  Render bepul "Web Service" tarifi doimiy fon jarayonini emas, faqat
#  HTTP so'rovlarga javob beruvchi xizmatni qo'llab-quvvatlaydi, shuning
#  uchun bot shu rejimda kichik aiohttp veb-serveri ichida ishlaydi va
#  Telegram xabar yuborganda "uyg'onadi".
# ============================================================
def run_webhook():
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    bot = build_bot()
    dp = build_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    async def health(request):
        return web.Response(text="🤖 Tezda Sotdim bot ishlayapti.")

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    SimpleRequestHandler(
        dispatcher=dp, bot=bot,
        secret_token=config.WEBHOOK_SECRET or None,
    ).register(app, path=config.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    logger.info("Webhook rejimida ishga tushmoqda: 0.0.0.0:%s, path=%s",
                config.PORT, config.WEBHOOK_PATH)
    web.run_app(app, host="0.0.0.0", port=config.PORT)


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN .env faylida ko'rsatilmagan!")
    if config.RUN_MODE == "webhook":
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
