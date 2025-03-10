import os
import logging
import threading
import time
import subprocess
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp

# ✅ جلب التوكن بأمان من Replit Secrets
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ خطأ: لم يتم العثور على توكن البوت! تأكد من إضافته في Secrets.")

# ✅ ضبط السجل لتسجيل الأخطاء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ إنشاء مجلد التحميلات
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# ✅ ضبط مسار FFmpeg (للتأكد من تثبيته في Replit)
FFMPEG_PATH = "/home/runner/.nix-profile/bin/ffmpeg"

# ✅ تثبيت FFmpeg تلقائيًا إذا لم يكن موجودًا
def install_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        logger.info("⚙️ يتم تثبيت FFmpeg...")
        subprocess.run(["nix-env", "-iA", "nixpkgs.ffmpeg"], check=True)
install_ffmpeg()

# ✅ ترحيب تلقائي كل 30 ثانية لإبقاء البوت نشطًا
def keep_bot_active(app):
    while True:
        try:
            app.bot.send_message(chat_id=YOUR_CHAT_ID, text="🤖 البوت يعمل بنجاح!")
        except Exception as e:
            logger.error(f"⚠️ خطأ في إرسال الرسالة الترحيبية: {e}")
        time.sleep(30)  # إرسال الرسالة كل 30 ثانية

# ================================================
# 🟢 أوامر البوت
# ================================================
async def start(update: Update, context):
    await update.message.reply_text("🎵 أهلاً بك! أرسل لي رابط قائمة تشغيل YouTube أو ألبوم وسأحوله لك إلى MP3.")

async def download_audio(update: Update, context):
    url = update.message.text
    chat_id = update.message.chat_id
    await update.message.reply_text("⏳ جاري تحميل الألبوم بالكامل... يرجى الانتظار.")

    # 🔹 تحميل جميع الملفات الصوتية من قائمة التشغيل
    files = await process_playlist(url)

    if files:
        for file_path in files:
            if os.path.exists(file_path):
                await context.bot.send_document(chat_id, document=open(file_path, "rb"))
                os.remove(file_path)  # حذف الملف بعد الإرسال لتوفير المساحة
        await update.message.reply_text("✅ تم تحميل جميع المقاطع الصوتية بنجاح!")
    else:
        await update.message.reply_text("❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط.")

# ================================================
# ⏬ معالجة تحميل الألبوم بالكامل
# ================================================
async def process_playlist(url):
    output_template = f"{DOWNLOADS_FOLDER}/%(playlist_index)s - %(title)s.%(ext)s"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'nocheckcertificate': True,
        'noplaylist': False,  # 🔹 تحميل الألبوم بالكامل وليس فيديو واحد فقط
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            files = [ydl.prepare_filename(entry).replace(".webm", ".mp3") for entry in info_dict.get("entries", [])]
            return files
    except Exception as e:
        logger.error(f"❌ خطأ في التحميل: {e}")
        return None

# ================================================
# 🤖 تشغيل بوت تيليجرام
# ================================================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    # 🔹 تشغيل رسالة الترحيب كل 30 ثانية
    threading.Thread(target=keep_bot_active, args=(app,), daemon=True).start()

    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling()

# ================================================
# 🌍 خادم Flask للحفاظ على تشغيل البوت
# ================================================
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "✅ البوت يعمل!"

def run_web():
    flask_app.run(host="0.0.0.0", port=8080)

# 🔹 تشغيل Flask مع بوت تيليجرام
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    main()
