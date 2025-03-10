```python
import os
import logging
import threading
import time
import subprocess
import shutil
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# ✅ جلب التوكن بأمان من Replit Secrets
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # أضف هذا في Secrets
if not TOKEN:
    raise ValueError("❌ خطأ: لم يتم العثور على توكن البوت!")

# ✅ ضبط السجل لتسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ إنشاء مجلد التحميلات
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# ✅ ضبط مسار FFmpeg
FFMPEG_PATH = "/home/runner/.nix-profile/bin/ffmpeg"

# ✅ تثبيت FFmpeg تلقائيًا
def install_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        logger.info("⚙️ يتم تثبيت FFmpeg...")
        subprocess.run(["nix-env", "-iA", "nixpkgs.ffmpeg"], check=True)
install_ffmpeg()

# ================================================
# 🟢 أوامر البوت المحسنة
# ================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🎵 أهلاً بك! استخدم أحد الأوامر التالية:
/audio <رابط> - تحميل صوت فردي
/video <رابط> - تحميل فيديو فردي
/album <رابط> - تحميل ألبوم كامل
"""
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith('/'):
        await update.message.reply_text("⚠️ الأمر غير معروف! استخدم /start للتعليمات")
    else:
        await update.message.reply_text("⚠️ أرسل رابطًا مع أحد الأوامر: /audio أو /video أو /album")

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.split()[0]
    url = update.message.text[len(command)+1:].strip()
    
    if not url:
        await update.message.reply_text("⚠️ يرجى إرسال الرابط مع الأمر!")
        return
    
    media_type = "audio" if "audio" in command else "video"
    is_playlist = True if "album" in command else False
    
    await process_download_wrapper(update, context, url, media_type, is_playlist)

# ================================================
# ⏬ معالجة التحميل المتقدمة
# ================================================
async def process_download_wrapper(update, context, url, media_type, is_playlist):
    chat_id = update.message.chat.id
    initial_msg = await update.message.reply_text("⏳ جاري التحميل... (قد يستغرق عدة دقائق)")
    
    try:
        if is_playlist:
            folder_path = await download_playlist(url, media_type)
            if folder_path:
                zip_path = shutil.make_archive(folder_path, 'zip', folder_path)
                await context.bot.send_document(chat_id, document=open(zip_path, 'rb'))
                shutil.rmtree(folder_path)
                os.remove(zip_path)
        else:
            file_path = await download_single(url, media_type)
            if file_path:
                if media_type == "audio":
                    await context.bot.send_audio(chat_id, audio=open(file_path, 'rb'))
                else:
                    await context.bot.send_video(chat_id, video=open(file_path, 'rb'))
                os.remove(file_path)
        
        await context.bot.delete_message(chat_id, initial_msg.message_id)
        await context.bot.send_message(chat_id, "✅ اكتمل التحميل بنجاح!")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await context.bot.send_message(chat_id, "❌ فشل التحميل! تأكد من صحة الرابط.")

async def download_playlist(url, media_type):
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_FOLDER}/%(playlist_title)s/%(title)s.%(ext)s',
        'ffmpeg_location': FFMPEG_PATH,
        'ignoreerrors': True,
        'nocheckcertificate': True,
    }
    
    if media_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(DOWNLOADS_FOLDER, info.get('playlist_title', 'playlist'))

async def download_single(url, media_type):
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
        'ffmpeg_location': FFMPEG_PATH,
        'nocheckcertificate': True,
    }
    
    if media_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3' if media_type == "audio" else '.mp4')

# ================================================
# 🤖 تشغيل البوت مع إدارة أفضل للموارد
# ================================================
def main():
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", download_media))
    app.add_handler(CommandHandler("video", download_media))
    app.add_handler(CommandHandler("album", download_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل خدمة الخلفية لإبقاء البوت نشطًا
    threading.Thread(target=keep_alive, daemon=True).start()
    
    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

# ================================================
# 🌍 خادم ويب محسن
# ================================================
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "✅ البوت يعمل بشكل طبيعي!"

def keep_alive():
    flask_app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()
```
