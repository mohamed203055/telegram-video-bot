import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# ✅ Load Telegram Bot Token from Replit Secrets
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Logging Setup for Debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Create Downloads Folder
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# ✅ Set Correct FFmpeg Path for Replit
FFMPEG_PATH = "/nix/store/.../bin/ffmpeg"  # Replace with actual path from `which ffmpeg`

# ✅ Store user session data (language & video link)
user_sessions = {}

# ================================================
# 🌍 LANGUAGE SELECTION
# ================================================
async def start(update: Update, context):
    """Send a welcome message and ask user for preferred language."""
    keyboard = [
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 Please choose your language / يرجى اختيار اللغة", reply_markup=reply_markup)

async def language_choice(update: Update, context):
    """Handle user’s language selection."""
    query = update.callback_query
    await query.answer()

    language = query.data
    user_sessions[query.message.chat_id] = language

    message_text = (
        "مرحبًا! أرسل رابط فيديو وسأساعدك في تحميله 🎥🎵"
        if language == "lang_ar" else
        "Hello! Send a video link, and I'll help you download it 🎥🎵"
    )
    await query.edit_message_text(message_text)

# ================================================
# 📩 VIDEO LINK HANDLER
# ================================================
async def download_menu(update: Update, context):
    """Display download options after user sends a video link."""
    url = update.message.text
    chat_id = update.message.chat_id
    user_sessions[chat_id] = url  # Store user link

    keyboard = [
        [InlineKeyboardButton("🎵 تحميل الصوت (MP3)", callback_data="audio")],
        [InlineKeyboardButton("📹 تحميل الفيديو (MP4)", callback_data="video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    lang = user_sessions.get(chat_id, "lang_en")
    message_text = "🎯 اختر نوع التحميل:" if lang == "lang_ar" else "🎯 Choose the type of download:"
    
    await update.message.reply_text(message_text, reply_markup=reply_markup)

# ================================================
# 🎬 DOWNLOAD HANDLER
# ================================================
async def download_media(update: Update, context):
    """Download the requested media file."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    url = user_sessions.get(chat_id)

    if not url:
        await query.message.reply_text("❌ No link found! Please send a valid video link.")
        return

    choice = query.data
    file_type = "الصوت" if choice == "audio" else "الفيديو"
    await query.message.reply_text(f"⏳ جارٍ تحميل {file_type}، يرجى الانتظار...")

    file_path = await process_download(url, choice)
    
    if file_path and os.path.exists(file_path):
        await context.bot.send_document(chat_id, document=open(file_path, "rb"))
        os.remove(file_path)  # ✅ Delete file after sending
    else:
        await query.edit_message_text("❌ Error downloading the file.")

# ================================================
# ⏬ PROCESS DOWNLOAD USING yt-dlp
# ================================================
async def process_download(url, choice):
    """Download the requested media file using yt-dlp."""
    output_template = f"{DOWNLOADS_FOLDER}/%(title)s.%(ext)s"
    
    ydl_opts = {
        'format': 'bestaudio/best' if choice == "audio" else 'best',
        'outtmpl': output_template,
        'ffmpeg_location': FFMPEG_PATH,  # ✅ Correct FFmpeg path for Replit
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if choice == "audio" else [],
        'cookiefile': "cookies.txt" if os.path.exists("cookies.txt") else None,  # ✅ Use cookies if available
        'quiet': False,
        'verbose': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return file_path.replace(".webm", ".mp3") if choice == "audio" else file_path
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        return None

# ================================================
# 🤖 TELEGRAM BOT RUNNER
# ================================================
def main():
    """Start the Telegram bot."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_menu))
    app.add_handler(CallbackQueryHandler(language_choice, pattern="^(lang_ar|lang_en)$"))
    app.add_handler(CallbackQueryHandler(download_media, pattern="^(audio|video)$"))

    logger.info("🤖 Bot is running...")
    app.run_polling()

# ================================================
# 🌍 FLASK SERVER TO KEEP BOT RUNNING ON REPLIT
# ================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ The bot is running!"

def run_web():
    """Run Flask server in a separate thread to keep Replit alive."""
    app.run(host="0.0.0.0", port=8080)

# ✅ Start Flask in a Thread & Run the Bot
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    main()
