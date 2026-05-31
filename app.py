import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 5696379479

# بيانات مؤقتة
user_stars = {}
forced_channels = []
delete_time = 60
after_message = "شكراً لاستخدامك البوت ❤️"

# القائمة الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_stars:
        user_stars[user_id] = 0

    buttons = [
        [InlineKeyboardButton("🛍️ متجر المقاطع", callback_data="store")],
        [InlineKeyboardButton("⭐ شحن النجوم", callback_data="stars")],
        [InlineKeyboardButton("🎁 كسب نجوم", callback_data="earn")],
        [InlineKeyboardButton("📦 روابطي", callback_data="links")]
    ]

    if user_id == OWNER_ID:
        buttons.append([InlineKeyboardButton("⚙️ لوحة المطور", callback_data="admin")])

    await update.message.reply_text(
        f"✨ أهلاً بك\n\nرصيدك: {user_stars[user_id]} ⭐",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "store":
        await query.message.reply_text("🛍️ متجر المقاطع (قريباً)")

    elif query.data == "stars":
        await query.message.reply_text("⭐ شحن النجوم (قريباً)")

    elif query.data == "earn":
        user_id = query.from_user.id
        link = f"https://t.me/fddfdfdfdbot?start=ref_{user_id}"

        await query.message.reply_text(
            f"🎁 رابط دعوتك:\n{link}\n\nكل شخص يدخل منه يعطيك نجوم"
        )

    elif query.data == "links":
        await query.message.reply_text("📦 روابط المحتوى (قريباً)")

    elif query.data == "admin":
        if query.from_user.id == OWNER_ID:
            admin_buttons = [
                [InlineKeyboardButton("➕ إضافة مقطع", callback_data="add_media")],
                [InlineKeyboardButton("⏳ مدة الحذف", callback_data="set_delete")],
                [InlineKeyboardButton("📢 الاشتراك الإجباري", callback_data="set_channels")],
                [InlineKeyboardButton("✉️ رسالة بعد الإرسال", callback_data="set_msg")]
            ]

            await query.message.reply_text(
                "⚙️ لوحة المطور",
                reply_markup=InlineKeyboardMarkup(admin_buttons)
            )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
