import time
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------- لاگ ----------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- تنظیمات ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # توکن از Railway Variables

REQUIRED_CHANNELS = [
    ("Grey_Grimoire", "گریمور خاکستری"),
    ("akharin_mahfel", "مدرسه آوانیس"),
    ("MAZUL_TIME", "مازول تایم"),
]

COOLDOWN_SECONDS = 600
user_cooldowns = {}
# -------------------------

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for channel, _ in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(f"@{channel}", user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await is_user_member(user.id, context):
        keyboard = [
            [InlineKeyboardButton(f"📢 عضویت در {name}", url=f"https://t.me/{ch}")]
            for ch, name in REQUIRED_CHANNELS
        ]
        keyboard.append(
            [InlineKeyboardButton("✅ بررسی عضویت من", callback_data="check_join")]
        )

        text = (
            f"👋 سلام {user.first_name}\n\n"
            "برای استفاده از ربات باید در کانال‌های زیر عضو باشی:\n\n"
        )
        for ch, name in REQUIRED_CHANNELS:
            text += f"• {name}: @{ch}\n"

        text += "\nبعد از عضویت روی «بررسی عضویت من» بزن"

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        return

    await update.message.reply_text(
        "✅ عضویت تایید شد\n\n"
        "🔢 آیدی عددی کاربر رو ارسال کن\n"
        "⏰ هر ۱۰ دقیقه یکبار"
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_member(query.from_user.id, context):
        await query.edit_message_text(
            "🎉 عضویتت تایید شد\n\n"
            "🔢 حالا آیدی عددی رو بفرست"
        )
    else:
        keyboard = [
            [InlineKeyboardButton(f"📢 عضویت در {name}", url=f"https://t.me/{ch}")]
            for ch, name in REQUIRED_CHANNELS
        ]
        keyboard.append(
            [InlineKeyboardButton("🔄 بررسی مجدد", callback_data="check_join")]
        )

        await query.edit_message_text(
            "❌ هنوز عضو همه کانال‌ها نیستی",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if not await is_user_member(user.id, context):
        await update.message.reply_text("❌ اول در کانال‌ها عضو شو /start")
        return

    now = time.time()
    last_time = user_cooldowns.get(user.id)

    if last_time and now - last_time < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last_time))
        await update.message.reply_text(
            f"⏳ {remaining} ثانیه دیگه صبر کن"
        )
        return

    if not text.isdigit() or not (5 <= len(text) <= 15):
        await update.message.reply_text("❌ آیدی عددی معتبر نیست")
        return

    user_cooldowns[user.id] = now

    tg_link = f"tg://user?id={text}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 پیدا شد", url=tg_link)]
    ])

    await update.message.reply_text(
        "✅ کاربر پیدا شد\n\n"
        "برای باز کردن چت روی دکمه زیر بزن",
        reply_markup=keyboard
    )

    logger.info(f"User {user.id} -> {text}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 راهنما\n\n"
        "/start شروع\n"
        "/help راهنما\n\n"
        "آیدی عددی بفرست تا لینک چت ساخته بشه"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    app.add_error_handler(error_handler)

    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
