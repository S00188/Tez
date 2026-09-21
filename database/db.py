import aiosqlite

from config import DATABASE_PATH

# MUHIM: barcha jadvallarda user_id maydoni users.telegram_id ga ishora qiladi
# (users.id emas) — bu handlerlar bilan mos kelishi va chalkashlikni oldini
# olish uchun ataylab shunday tanlangan.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    balance INTEGER NOT NULL DEFAULT 0,
    referred_by INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    is_blocked INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_code TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    telegram_file_id TEXT,
    caption TEXT,
    text TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    channel_message_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    published_at TEXT,
    completed_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    public_code TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    telegram_file_id TEXT,
    caption TEXT,
    text TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    channel_message_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    published_at TEXT,
    completed_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,            -- AD_PUBLICATION | ORDER_PUBLICATION | CONTACT_UNLOCK
    ad_id INTEGER,
    order_id INTEGER,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'UZS',
    receipt_file_id TEXT,
    status TEXT NOT NULL DEFAULT 'WAITING_RECEIPT',
    reject_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    approved_at TEXT,
    approved_by INTEGER
);

CREATE TABLE IF NOT EXISTS contact_unlocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    developer_user_id INTEGER NOT NULL,
    payment_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    approved_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT,
    updated_by INTEGER
);

CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_code TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS admin_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    action_type TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

DEFAULT_SETTINGS = {
    "ad_price": "34990",
    "order_price": "34990",
    "contact_price": "25000",
    "card_number": "9860160605433400",
    "card_holder": "T. K.",
    "admins": "",
    "image_required": "1",
    "image_format": "16:9, hajmi 20MB gacha",
    "max_active_ads": "5",
    "max_active_orders": "5",
    "referral_enabled": "1",
    "referral_bonus": "5000",
    "start_text": "🚀 Tezda Sotdim — raqamli mahsulotlar bozori!\n\n📢 Tayyor dasturingizni e'lon qiling yoki 🔵 kerakli dasturga zakaz bering.\n\nPastdagi menyudan bo'limni tanlang:",
    "ad_guide": "📢 E'lon berish\n\n📝 Dasturingiz haqida yozilgan matn va rasmni bitta xabarda yuboring.\n\n📐 Rasm 16:9 formatda bo'lishi tavsiya etiladi.\n\n👇 E'loningizni yuboring.",
    "order_guide": "🔵 Dasturga zakaz berish\n\nSizga kerak bo'lgan bot, WebApp, sayt, mobil ilova yoki boshqa dastur haqida xabaringizni yuboring.\n\n📝 Xabaringizni o'zingiz xohlagan tarzda yozishingiz mumkin.\n\n📌 Qancha batafsil yozsangiz, dasturchilar uchun shuncha tushunarli bo'ladi.",
    "ad_guarantee": "❓ Botim sotilishiga kafolat bormi?\n\nE'lon joylashtirilishi — botingiz albatta sotiladi degan kafolatni anglatmaydi.\n\nBizning xizmatimiz botingizni kanal auditoriyasiga e'lon sifatida taqdim etish va potensial xaridorlarga yetkazib berishdan iborat.\n\nXaridorning qaroriga botning narxi, sifati, funksiyalari, talabi va boshqa omillar ta'sir qilishi mumkin.",
    "order_guarantee": "❓ Zakaz bajarilishiga kafolat bormi?\n\nZakaz joylashtirilishi — albatta bajariladi degan kafolatni anglatmaydi.\n\nBizning xizmatimiz talabingizni dasturchilar auditoriyasiga yetkazib berishdan iborat.\n\nSiz va dasturchi o'rtasida narx, shart va boshqa omillar kelishiladi.",
    "sign_text": "🤖 @tezda_sotdim_bot — siz izlayotgan tayyor botlar sotuvda!",
    "rules_text": "ℹ️ Qoidalar\n\n• Bot faqat raqamli mahsulotlar (bot, webapp, sayt, dastur) e'loni uchun.\n• E'lon va zakaz kontenti qonunga zid bo'lmasligi kerak.\n• Firibgarlik va aldash qat'iyan man etiladi.\n• Kanal orqali shikoyat qilish mumkin.\n• Platforma sotuv/bajarilish uchun kafolat bermaydi — bu aloqa o'rnatuvchi vosita.",
}

_conn = None


async def get_db():
    global _conn
    if _conn is None:
        from pathlib import Path
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = await aiosqlite.connect(DATABASE_PATH)
        _conn.row_factory = aiosqlite.Row
        await _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    cur = await db.execute("SELECT COUNT(*) FROM settings")
    if (await cur.fetchone())[0] == 0:
        await db.executemany(
            "INSERT INTO settings(key, value) VALUES (?, ?)",
            list(DEFAULT_SETTINGS.items()),
        )
    else:
        # yangi qo'shilgan sozlamalarni mavjud bazaga to'ldirish
        cur = await db.execute("SELECT key FROM settings")
        existing = {r[0] for r in await cur.fetchall()}
        missing = [(k, v) for k, v in DEFAULT_SETTINGS.items() if k not in existing]
        if missing:
            await db.executemany(
                "INSERT INTO settings(key, value) VALUES (?, ?)", missing)
    await db.commit()


async def close_db():
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None
