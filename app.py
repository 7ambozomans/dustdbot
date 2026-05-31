import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 5696379479

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("🛍️ متجر المقاطع", callback_data="store")],
        [InlineKeyboardButton("⭐ شحن النجوم", callback_data="stars")],
        [InlineKeyboardButton("🎁 ربح مجاني", callback_data="free")],
        [InlineKeyboardButton("📦 طلباتي", callback_data="orders")],
        [InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin")]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "✨ أهلاً بك في بوت تجربة\n\nاختر من القائمة:",
        reply_markup=keyboard
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
