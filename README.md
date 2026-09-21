# 🔥 Tezda Sotdim — Telegram Digital Market

Raqamli mahsulotlar (bot / web-app / sayt / kanal va h.k.) uchun
e'lon berish + buyurtma qilish + kontakt-unlock bozori.

## Lokal ishga tushirish (polling)
1. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. `.env` faylni `.env.example` dan nusxalab, `BOT_TOKEN` va `ADMIN_IDS`ni to'ldiring
   (`RUN_MODE=polling` — standart holat, o'zgartirish shart emas)
3. `./bot.sh`

## Struktura
- `config.py` / `.env` — sozlamalar
- `database/` — SQLite schema + repo (`repo.py`)
- `keyboards/` — Inline/Reply keyboard quruvchilar
- `handlers/user|admin` — aiogram 3 router + FSM handlerlar
- `states/` — StateGroup'lar (`AdStates`, `OrderStates`, ...)
- `services/` — to'lov oqimi, kanalga post qilish yordamchilari
- `main.py` — polling **va** webhook rejimlarini boshqaradi (`RUN_MODE`)

## Admin
`ADMIN_IDS`'dagi foydalanuvchi `/admin` orqali panel ochadi: cheklarni
tasdiqlash/rad etish, narx-sozlamalar, shikoyatlar, statistika, reklama.

---

## ☁️ Render'ning bepul tarifiga joylashtirish

Render bepul "Web Service" tarifi doimiy ishlab turuvchi fon jarayonini
qo'llab-quvvatlamaydi — u faqat HTTP so'rovlarga javob beruvchi xizmatni
beradi va **15 daqiqa harakatsizlikdan keyin "uxlab qoladi"**. Shu sababli
bot `RUN_MODE=webhook` rejimida — kichik HTTP-server ichida — ishlaydi:
Telegramdan xabar kelganda server "uyg'onadi" va uni qayta ishlaydi.

> ⚠️ **MUHIM CHEKLOV — ma'lumotlar bazasi o'chib ketishi mumkin**
> Bepul tarifda doimiy disk yo'q. Har safar qayta deploy qilganda yoki
> server uzoq vaqt harakatsizlikdan keyin qayta ishga tushganda
> (Render buni ba'zan avtomatik ham qilib turadi), `data/bot.db`
> fayli **tozalanadi** — barcha foydalanuvchi, balans, e'lon va zakaz
> ma'lumotlari yo'qoladi. Bu SQLite + bepul tarifning tabiiy cheklovi;
> uni hal qilish uchun tashqi (Render tashqarisidagi) bazaga
> (masalan, Supabase/Neon Postgres) ulanish kerak bo'ladi.

> ⏱ **Sovuq boshlanish (cold start)**: uxlab qolgan xizmat birinchi
> xabarga ~30–60 soniyada javob berishi mumkin, chunki server avval
> "uyg'onishi" kerak.

### 1-usul: Blueprint (`render.yaml`) orqali — eng oson
1. Ushbu loyihani GitHub'ga yuklang (git repo sifatida).
2. Render Dashboard → **New** → **Blueprint** → shu repo'ni tanlang.
   Render `render.yaml` faylini o'qib, xizmatni avtomatik tuzadi.
3. So'ralganda quyidagi maxfiy o'zgaruvchilarni kiriting:
   - `BOT_TOKEN` — @BotFather'dan olingan token
   - `ADMIN_IDS` — adminlarning Telegram ID'lari (vergul bilan)
   - `BOT_USERNAME` — bot username'i (`@`siz)
   - `CHANNEL_ID` — kanal ID'si (masalan `-1001234567890`)
4. Deploy tugagach, Render sizga `https://<nom>.onrender.com` manzilini
   beradi — `WEBHOOK_HOST`ni qo'lda kiritish shart emas, u avtomatik
   aniqlanadi (`RENDER_EXTERNAL_URL`).
5. Bot ishga tushgach, adminlarga "✅ Bot ishga tushdi!" xabari keladi.

### 2-usul: Qo'lda ("New Web Service")
1. Render Dashboard → **New** → **Web Service** → GitHub repo'ni ulang.
2. **Environment**: `Python 3`
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `python main.py`
5. **Plan**: `Free`
6. **Environment Variables** bo'limida qo'shing:
   | Kalit | Qiymat |
   |---|---|
   | `RUN_MODE` | `webhook` |
   | `BOT_TOKEN` | bot tokeningiz |
   | `ADMIN_IDS` | `111111111,222222222` |
   | `BOT_USERNAME` | `TezdaSotdimBot` |
   | `CHANNEL_ID` | `-1001234567890` |
   | `DATABASE_PATH` | `data/bot.db` |
   | `WEBHOOK_SECRET` | tasodifiy uzun matn (masalan `openssl rand -hex 24`) |
7. **Health Check Path**: `/health`
8. **Create Web Service** bosing — Render avtomatik build va deploy qiladi.

### Botni "uxlab qolishidan" saqlash (ixtiyoriy)
Cold start'ni kamaytirish uchun bepul monitoring xizmatidan
(masalan [UptimeRobot](https://uptimerobot.com)) foydalanib,
`https://<nom>.onrender.com/health` manzilini har 10–14 daqiqada bir marta
so'rab turishni sozlashingiz mumkin — bu xizmatni doim uyg'oq tutadi
(lekin baribir SQLite'ning yuqoridagi cheklovini bartaraf etmaydi).
