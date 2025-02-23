import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, CallbackContext
)
import yt_dlp

# ✅ Load Telegram Bot Token from Environment Variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Directory for Downloads
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# ✅ Store user-selected video links
user_links = {}

# ============================================
# 🌍 LANGUAGE SELECTION HANDLER
# ============================================
async def start(update: Update, context: CallbackContext):
    """Send a welcome message with language selection."""
    keyboard = [
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎯 Please choose your language / يرجى اختيار اللغة", reply_markup=reply_markup
    )

async def language_choice(update: Update, context: CallbackContext):
    """Set user language preference."""
    query = update.callback_query
    await query.answer()

    context.user_data['language'] = query.data
    message_text = (
        "مرحبًا! أرسل رابط فيديو وسأساعدك في تحميله 🎥🎵"
        if query.data == "lang_ar" else
        "Hello! Send a video link, and I'll help you download it 🎥🎵"
    )

    await query.edit_message_text(message_text)

# ============================================
# 📩 VIDEO LINK HANDLER
# ============================================
async def download_menu(update: Update, context: CallbackContext):
    """Display download options after receiving a video link."""
    url = update.message.text
    chat_id = update.message.chat_id
    user_links[chat_id] = url  # Store user link

    keyboard = [
        [InlineKeyboardButton("🎵 تحميل الصوت (MP3)", callback_data="audio")],
        [InlineKeyboardButton("📹 تحميل الفيديو (MP4)", callback_data="video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    language = context.user_data.get('language', 'lang_en')
    message_text = "🎯 اختر نوع التحميل:" if language == 'lang_ar' else "🎯 Choose the type of download:"

    await update.message.reply_text(message_text, reply_markup=reply_markup)

# ============================================
# 🎬 DOWNLOAD HANDLER
# ============================================
async def download_media(update: Update, context: CallbackContext):
    """Process the download request for audio/video."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    url = user_links.get(chat_id)

    if not url:
        await query.message.reply_text("❌ لم أتمكن من العثور على الرابط. أرسل الرابط من جديد.")
        return

    choice = query.data
    await query.message.reply_text("⏳ جارٍ التحميل، يرجى الانتظار...")

    file_path = await process_download(url, choice)

    if file_path:
        await context.bot.send_document(chat_id, document=open(file_path, "rb"))
        os.remove(file_path)  # Delete the file after sending
    else:
        await query.message.reply_text("❌ حدث خطأ أثناء التحميل.")

# ============================================
# ⏬ PROCESS DOWNLOAD USING yt-dlp
# ============================================
async def process_download(url, choice):
    """Download the requested media using yt-dlp with cookies and ffmpeg."""
    output_template = f"{DOWNLOADS_FOLDER}/%(title)s.%(ext)s"
    
    ydl_opts = {
        'format': 'bestaudio/best' if choice == "audio" else 'best',
        'outtmpl': output_template,
        'ffmpeg_location': "./ffmpeg-7.0.2-amd64-static/ffmpeg",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if choice == "audio" else [],
        'cookiefile': './cookies.txt' if os.path.exists("cookies.txt") else None,
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
        logger.error(f"❌ Download Error: {e}")
        return None

# ============================================
# 🤖 TELEGRAM BOT RUNNER
# ============================================
def main():
    """Run the Telegram bot."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_menu))
    app.add_handler(CallbackQueryHandler(language_choice, pattern="^(lang_ar|lang_en)$"))
    app.add_handler(CallbackQueryHandler(download_media, pattern="^(audio|video)$"))

    logger.info("🤖 The bot is now running...")
    app.run_polling()

# ============================================
# 🌍 FLASK SERVER TO KEEP BOT RUNNING
# ============================================
app = Flask(__name__)

@app.route('/')
def home():
    return "The bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# ✅ Start Flask in a Separate Thread
threading.Thread(target=run_web, daemon=True).start()

# ✅ Start the Bot
if __name__ == "__main__":
    main()
