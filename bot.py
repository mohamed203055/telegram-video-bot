import os
import logging
import threading
import subprocess
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
FFMPEG_PATH = "/home/runner/.nix-profile/bin/ffmpeg"
FFPROBE_PATH = "/home/runner/.nix-profile/bin/ffprobe"

# ✅ Ensure ffmpeg is installed
def install_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        logger.info("Installing ffmpeg...")
        subprocess.run(["nix-env", "-iA", "nixpkgs.ffmpeg"], check=True)
install_ffmpeg()

# ✅ Store user session data (language & video link)
user_sessions = {}

# ================================================
# 🌍 LANGUAGE SELECTION
# ================================================
async def start(update: Update, context):
    keyboard = [[InlineKeyboardButton("العربية", callback_data="lang_ar")],
                [InlineKeyboardButton("English", callback_data="lang_en")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 Please choose your language / يرجى اختيار اللغة", reply_markup=reply_markup)

async def language_choice(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_sessions[query.message.chat_id] = query.data
    message_text = "مرحبًا! أرسل رابط فيديو وسأساعدك في تحميله 🎥🎵" if query.data == "lang_ar" else "Hello! Send a video link, and I'll help you download it 🎥🎵"
    await query.edit_message_text(message_text)

# ================================================
# 📩 VIDEO LINK HANDLER
# ================================================
async def download_menu(update: Update, context):
    url = update.message.text
    chat_id = update.message.chat_id
    user_sessions[chat_id] = url
    keyboard = [[InlineKeyboardButton("🎵 تحميل الصوت (MP3)", callback_data="audio")],
                [InlineKeyboardButton("📹 تحميل الفيديو (MP4)", callback_data="video")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    lang = user_sessions.get(chat_id, "lang_en")
    message_text = "🎯 اختر نوع التحميل:" if lang == "lang_ar" else "🎯 Choose the type of download:"
    await update.message.reply_text(message_text, reply_markup=reply_markup)

# ================================================
# 🎬 DOWNLOAD HANDLER
# ================================================
async def download_media(update: Update, context):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    url = user_sessions.get(chat_id)
    if not url:
        await query.message.reply_text("❌ No link found! Please send a valid video link.")
        return
    choice = query.data
    await query.message.reply_text(f"⏳ Downloading... Please wait")
    file_path = await process_download(url, choice)
    if file_path and os.path.exists(file_path):
        await context.bot.send_document(chat_id, document=open(file_path, "rb"))
        os.remove(file_path)
    else:
        await query.edit_message_text("❌ Error downloading the file.")

# ================================================
# ⏬ PROCESS DOWNLOAD USING yt-dlp
# ================================================
async def process_download(url, choice):
    output_template = f"{DOWNLOADS_FOLDER}/%(title)s.%(ext)s"
    ydl_opts = {
        'format': 'bestaudio/best' if choice == "audio" else 'best',
        'outtmpl': output_template,
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}] if choice == "audio" else [],
        'nocheckcertificate': True,
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
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "✅ The bot is running!"

def run_web():
    flask_app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    main()
