from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import BadRequest
import random
import string
import sqlite3
import logging

# === Setup Logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === CONFIG ===
BOT_TOKEN = "8155036128:AAFYCMal39Fa-g-Ri0cjcFb7sN8aUod4RT0"
BOT_USERNAME = "LinkVidBot_bot"
CHANNEL_ID = "@Movies_bot21"  # ✅ Use the new public username
CHANNEL_INVITE_LINK = "https://t.me/Movies_bot21"


# === Database Setup ===
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS videos (code TEXT PRIMARY KEY, file_id TEXT)")

# === Generate Unique Code ===
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# === Check if user is member of the required channel ===
async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except BadRequest:
        return False

# === Admin sends video ===
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    file_id = update.message.video.file_id

    # Generate unique code
    code = generate_code()
    while cursor.execute("SELECT * FROM videos WHERE code=?", (code,)).fetchone() is not None:
        code = generate_code()

    cursor.execute("INSERT INTO videos VALUES (?, ?)", (code, file_id))
    conn.commit()

    link = f"https://t.me/{BOT_USERNAME}?start={code}"
    await update.message.reply_text(f"Here’s your unique video link:\n{link}")
    logging.info(f"Generated new link: {link} for user: {user.username or user.id}")

# === When user clicks start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if user is a member
    if not await is_member(context.bot, user_id):
        buttons = [
            [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_INVITE_LINK)],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_subs")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "Please join our channel to access the video:",
            reply_markup=reply_markup
        )
        return

    # User is already a member
    if context.args:
        code = context.args[0]
        cursor.execute("SELECT file_id FROM videos WHERE code=?", (code,))
        result = cursor.fetchone()

        if result:
            await update.message.reply_video(result[0])
        else:
            await update.message.reply_text("⚠️ Invalid or expired link.")
    else:
        await update.message.reply_text("👋 Welcome! Send a video to generate a shareable link.")

# === Callback when user clicks "I've Joined" ===
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_member(context.bot, user_id):
        await query.edit_message_text("❌ You're not a member yet. Please join the channel and try again.")
    else:
        await query.edit_message_text("✅ You’ve joined! Send the link again to get your video.")

# === Bot Setup ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subs"))

print("✅ Bot is running...")
app.run_polling()
