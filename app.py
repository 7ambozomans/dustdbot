import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = 5696379479


def main_menu(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🛍️ متجر المقاطع", callback_data="store"),
            InlineKeyboardButton("⭐ شحن النجوم", callback_data="stars")
        ],
        [
            InlineKeyboardButton("🎁 ربح مجاني", callback_data="free"),
            InlineKeyboardButton("📦 طلباتي", callback_data="orders")
        ]
    ]

    if user_id == OWNER_ID:
        keyboard.append([
            InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin")
        ])

    return InlineKeyboardMarkup(keyboard)


def admin_menu():
    keyboard = [
        [
            InlineKeyboardButton("➕ إضافة مقطع", callback_data="add"),
            InlineKeyboardButton("🔗 إنشاء رابط", callback_data="link")
        ],
        [
            InlineKeyboardButton("⏳ مدة الحذف", callback_data="delete"),
            InlineKeyboardButton("📢 اشتراك إجباري", callback_data="force")
        ],
        [
            InlineKeyboardButton("⭐ إعداد النجوم", callback_data="coins"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
        ],
        [
            InlineKeyboardButton("⬅️ رجوع", callback_data="back")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ أهلاً بك في بوت تجربة\n\nاختر من القائمة:",
        reply_markup=main_menu(update.effective_user.id)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin":
        await query.message.edit_text(
            "⚙️ لوحة تحكم المطور",
            reply_markup=admin_menu()
        )

    elif query.data == "back":
        await query.message.edit_text(
            "✨ القائمة الرئيسية",
            reply_markup=main_menu(query.from_user.id)
        )

    elif query.data == "store":
        await query.message.edit_text(
            "🛍️ متجر المقاطع\n\nلا يوجد مقاطع حالياً",
            reply_markup=main_menu(query.from_user.id)
        )

    elif query.data == "stars":
        await query.message.edit_text(
            "⭐ شحن النجوم\n\nاختر الباقة لاحقاً",
            reply_markup=main_menu(query.from_user.id)
        )

    elif query.data == "free":
        await query.message.edit_text(
            "🎁 الربح المجاني\n\nشارك رابط دعوتك",
            reply_markup=main_menu(query.from_user.id)
        )

    elif query.data == "orders":
        await query.message.edit_text(
            "📦 لا يوجد طلبات",
            reply_markup=main_menu(query.from_user.id)
        )

    elif query.data == "add":
        await query.message.edit_text(
            "➕ أرسل الآن المقطع الذي تريد إضافته",
            reply_markup=admin_menu()
        )

    elif query.data == "link":
        await query.message.edit_text(
            "🔗 إنشاء رابط جديد",
            reply_markup=admin_menu()
        )

    elif query.data == "delete":
        await query.message.edit_text(
            "⏳ تحديد مدة حذف الوسائط",
            reply_markup=admin_menu()
        )

    elif query.data == "force":
        await query.message.edit_text(
            "📢 إعداد الاشتراك الإجباري",
            reply_markup=admin_menu()
        )

    elif query.data == "coins":
        await query.message.edit_text(
            "⭐ إعداد أسعار النجوم",
            reply_markup=admin_menu()
        )

    elif query.data == "stats":
        await query.message.edit_text(
            "📊 الإحصائيات\n\n0 مستخدم",
            reply_markup=admin_menu()
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
