import os
import json
import asyncio
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 5696379479
DATA_FILE = "data.json"

# ------------------ قاعدة البيانات ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "media": {},
            "links": {},
            "forced_channels": [],
            "delete_time": 60,
            "after_message": "شكراً لاستخدام البوت ❤️",
            "star_price": 1,
            "ref_reward": 5
        }

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

db = load_data()

# ------------------ المستخدم ------------------

def ensure_user(user_id):
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "stars": 0,
            "purchases": []
        }
        save_data()

# ------------------ القوائم ------------------

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🛍️ متجر المقاطع", callback_data="store")],
        [InlineKeyboardButton("⭐ شحن النجوم", callback_data="charge")],
        [InlineKeyboardButton("🎁 كسب نجوم", callback_data="earn")],
        [InlineKeyboardButton("📦 طلباتي", callback_data="orders")]
    ]

    if user_id == OWNER_ID:
        buttons.append(
            [InlineKeyboardButton("⚙️ لوحة المطور", callback_data="admin")]
        )

    return InlineKeyboardMarkup(buttons)

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة مقطع", callback_data="add_media")],
        [InlineKeyboardButton("📢 القنوات الإجبارية", callback_data="channels")],
        [InlineKeyboardButton("⏳ مدة الحذف", callback_data="delete_time")],
        [InlineKeyboardButton("✉️ رسالة بعد الإرسال", callback_data="after_msg")],
        [InlineKeyboardButton("⭐ سعر النجوم", callback_data="star_price")]
    ])

# ------------------ /start ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id)

    if context.args:
        ref = context.args[0]
        if ref.startswith("ref_"):
            inviter = ref.replace("ref_", "")
            if inviter != str(user.id):
                ensure_user(inviter)
                db["users"][inviter]["stars"] += db["ref_reward"]
                save_data()

    stars = db["users"][str(user.id)]["stars"]

    await update.message.reply_text(
        f"✨ أهلاً بك\n\nرصيدك: {stars} ⭐",
        reply_markup=main_menu(user.id)
    )

# ------------------ الأزرار ------------------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    if query.data == "store":
        if not db["media"]:
            await query.message.reply_text("لا يوجد مقاطع حالياً")
            return

        for mid, item in db["media"].items():
            txt = f"🎬 {item['name']}\n⭐ السعر: {item['price']}"
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("شراء", callback_data=f"buy_{mid}")]
            ])
            await query.message.reply_text(txt, reply_markup=btn)

    elif query.data.startswith("buy_"):
        mid = query.data.replace("buy_", "")
        media = db["media"][mid]

        ensure_user(uid)

        if db["users"][str(uid)]["stars"] < media["price"]:
            await query.message.reply_text("رصيدك غير كافٍ")
            return

        db["users"][str(uid)]["stars"] -= media["price"]
        save_data()

        sent = await query.message.reply_text(
            f"تم شراء: {media['name']}"
        )

        await asyncio.sleep(db["delete_time"])
        await sent.delete()

    elif query.data == "earn":
        link = f"https://t.me/fddfdfdfdbot?start=ref_{uid}"

        await query.message.reply_text(
            f"🎁 رابط دعوتك:\n{link}"
        )

    elif query.data == "charge":
        await query.message.reply_text(
            f"⭐ سعر النجمة: {db['star_price']}"
        )

    elif query.data == "orders":
        await query.message.reply_text("طلباتك محفوظة")

    elif query.data == "admin" and uid == OWNER_ID:
        await query.message.reply_text(
            "⚙️ لوحة المطور",
            reply_markup=admin_menu()
        )

    elif query.data == "add_media":
        context.user_data["await_media"] = True
        await query.message.reply_text(
            "أرسل الآن المقطع مع الاسم بالشكل:\nاسم المقطع|السعر"
        )

# ------------------ استقبال المقاطع ------------------

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_media"):
        return

    if not update.message.caption:
        await update.message.reply_text("اكتب الاسم والسعر في الكابشن")
        return

    try:
        name, price = update.message.caption.split("|")
        price = int(price)
    except:
        await update.message.reply_text("الصيغة: الاسم|السعر")
        return

    media_id = str(uuid.uuid4())

    file_id = None
    media_type = None

    if update.message.video:
        file_id = update.message.video.file_id
        media_type = "video"

    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        media_type = "photo"

    elif update.message.voice:
        file_id = update.message.voice.file_id
        media_type = "voice"

    if not file_id:
        await update.message.reply_text("نوع غير مدعوم")
        return

    db["media"][media_id] = {
        "name": name,
        "price": price,
        "file_id": file_id,
        "type": media_type
    }

    save_data()
    context.user_data["await_media"] = False

    await update.message.reply_text("تمت إضافة المقطع ✅")

# ------------------ تشغيل ------------------

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(
        filters.ALL,
        receive_media
    ))

    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
