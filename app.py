import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ==========================
# الإعدادات
# ==========================

TOKEN = "8800609433:AAGxXFySv0pVYjAvKFqGxum7xL1aFt_acdE"
ADMIN_ID = 5696379479

# [] = بدون اشتراك إجباري
FORCE_CHANNELS = [ t.me/dustnum ]

DELETE_AFTER = 30
REFERRAL_REWARD = 10

# ==========================
# قاعدة البيانات
# ==========================

conn = sqlite3.connect("bot.db", check_same_thread=False)
db = conn.cursor()

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    stars INTEGER DEFAULT 0
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    media_type TEXT,
    price INTEGER
)
""")

conn.commit()

waiting_price = {}

# ==========================
# أدوات
# ==========================

def add_user(user_id):
    db.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()

def get_stars(user_id):
    row = db.execute(
        "SELECT stars FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    return row[0] if row else 0

async def check_subscription(bot, user_id):
    if not FORCE_CHANNELS:
        return True

    for channel in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status in ["left", "kicked"]:
                return False
        except:
            return False

    return True

# ==========================
# start
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    if not await check_subscription(context.bot, user_id):
        await update.message.reply_text(
            "اشترك بالقنوات أولاً ثم أرسل /start"
        )
        return

    keyboard = [
        [InlineKeyboardButton("🛒 المتجر", callback_data="store")],
        [InlineKeyboardButton("⭐ رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🎁 رابط الدعوة", callback_data="invite")]
    ]

    await update.message.reply_text(
        "أهلاً بك في المتجر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================
# المتجر
# ==========================

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    items = db.execute(
        "SELECT id, price FROM media"
    ).fetchall()

    if not items:
        await query.message.reply_text("لا يوجد منتجات")
        return

    buttons = []

    for item in items:
        buttons.append([
            InlineKeyboardButton(
                f"شراء المنتج #{item[0]} ⭐{item[1]}",
                callback_data=f"buy_{item[0]}"
            )
        ])

    await query.message.reply_text(
        "المتجر:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==========================
# شراء
# ==========================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    media_id = int(query.data.split("_")[1])

    stars = get_stars(user_id)

    media = db.execute(
        "SELECT file_id, media_type, price FROM media WHERE id=?",
        (media_id,)
    ).fetchone()

    if not media:
        await query.message.reply_text("غير موجود")
        return

    file_id, media_type, price = media

    if stars < price:
        await query.message.reply_text("رصيدك غير كافي")
        return

    db.execute(
        "UPDATE users SET stars = stars - ? WHERE user_id=?",
        (price, user_id)
    )
    conn.commit()

    if media_type == "video":
        msg = await query.message.reply_video(file_id)

    elif media_type == "photo":
        msg = await query.message.reply_photo(file_id)

    else:
        msg = await query.message.reply_audio(file_id)

    await query.message.reply_text(
        "تم الإرسال وسيُحذف تلقائياً"
    )

    await asyncio.sleep(DELETE_AFTER)

    try:
        await msg.delete()
    except:
        pass

# ==========================
# الرصيد
# ==========================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stars = get_stars(query.from_user.id)

    await query.message.reply_text(
        f"رصيدك: ⭐ {stars}"
    )

# ==========================
# الدعوات
# ==========================

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"

    await query.message.reply_text(
        f"شارك الرابط:\n{link}"
    )

# ==========================
# إضافة منتج
# ==========================

async def addmedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "/addmedia السعر"
        )
        return

    waiting_price[update.effective_user.id] = int(context.args[0])

    await update.message.reply_text(
        "أرسل الآن الفيديو أو الصورة أو الصوت"
    )

# ==========================
# استقبال الوسائط
# ==========================

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    if user_id not in waiting_price:
        return

    price = waiting_price[user_id]

    if update.message.video:
        file_id = update.message.video.file_id
        media_type = "video"

    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        media_type = "photo"

    elif update.message.audio:
        file_id = update.message.audio.file_id
        media_type = "audio"

    else:
        await update.message.reply_text("نوع غير مدعوم")
        return

    db.execute(
        "INSERT INTO media (file_id, media_type, price) VALUES (?, ?, ?)",
        (file_id, media_type, price)
    )

    conn.commit()

    del waiting_price[user_id]

    await update.message.reply_text(
        "تمت إضافة المنتج"
    )

# ==========================
# إضافة نجوم
# ==========================

async def addstars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "/addstars user_id amount"
        )
        return

    target = int(context.args[0])
    amount = int(context.args[1])

    db.execute(
        "UPDATE users SET stars = stars + ? WHERE user_id=?",
        (amount, target)
    )

    conn.commit()

    await update.message.reply_text("تمت الإضافة")

# ==========================
# تشغيل
# ==========================

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addmedia", addmedia))
app.add_handler(CommandHandler("addstars", addstars))

app.add_handler(CallbackQueryHandler(store, pattern="store"))
app.add_handler(CallbackQueryHandler(balance, pattern="balance"))
app.add_handler(CallbackQueryHandler(invite, pattern="invite"))
app.add_handler(CallbackQueryHandler(buy, pattern="buy_"))

app.add_handler(
    MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO,
        receive_media
    )
)

print("البوت يعمل...")

app.run_polling()
