import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8800609433:AAGxXFySv0pVYjAvKFqGxum7xL1aFt_acdE"
ADMIN_ID = 5696379479
DELETE_AFTER = 20

conn = sqlite3.connect("bot.db", check_same_thread=False)
db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, stars INTEGER DEFAULT 0)")
db.execute("CREATE TABLE IF NOT EXISTS media (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT, media_type TEXT, price INTEGER)")
conn.commit()

waiting_price = {}

def add_user(user_id):
    db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_stars(user_id):
    row = db.execute("SELECT stars FROM users WHERE user_id=?", (user_id,)).fetchone()
    return row[0] if row else 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("🛒 المتجر", callback_data="store")],
        [InlineKeyboardButton("⭐ رصيدي", callback_data="balance")]
    ]

    await update.message.reply_text(
        "أهلاً بك",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    items = db.execute("SELECT id, price FROM media").fetchall()

    if not items:
        await query.message.reply_text("لا يوجد منتجات")
        return

    buttons = []

    for item in items:
        buttons.append([
            InlineKeyboardButton(
                f"شراء #{item[0]} ⭐{item[1]}",
                callback_data=f"buy_{item[0]}"
            )
        ])

    await query.message.reply_text(
        "المتجر",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stars = get_stars(query.from_user.id)
    await query.message.reply_text(f"رصيدك: ⭐ {stars}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    media_id = int(query.data.split("_")[1])

    media = db.execute(
        "SELECT file_id, media_type, price FROM media WHERE id=?",
        (media_id,)
    ).fetchone()

    if not media:
        await query.message.reply_text("غير موجود")
        return

    file_id, media_type, price = media

    if get_stars(user_id) < price:
        await query.message.reply_text("رصيدك غير كافي")
        return

    db.execute("UPDATE users SET stars=stars-? WHERE user_id=?", (price, user_id))
    conn.commit()

    if media_type == "video":
        msg = await query.message.reply_video(file_id)
    elif media_type == "photo":
        msg = await query.message.reply_photo(file_id)
    else:
        msg = await query.message.reply_audio(file_id)

    await asyncio.sleep(DELETE_AFTER)

    try:
        await msg.delete()
    except:
        pass

async def addmedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("/addmedia السعر")
        return

    waiting_price[update.effective_user.id] = int(context.args[0])

    await update.message.reply_text("أرسل الوسيط الآن")

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
        return

    db.execute(
        "INSERT INTO media (file_id, media_type, price) VALUES (?, ?, ?)",
        (file_id, media_type, price)
    )
    conn.commit()

    del waiting_price[user_id]

    await update.message.reply_text("تمت الإضافة")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addmedia", addmedia))

app.add_handler(CallbackQueryHandler(store, pattern="store"))
app.add_handler(CallbackQueryHandler(balance, pattern="balance"))
app.add_handler(CallbackQueryHandler(buy, pattern="buy_"))

app.add_handler(
    MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO,
        receive_media
    )
)

print("البوت يعمل...")
app.run_polling()
