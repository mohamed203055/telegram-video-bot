import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# الحصول على التوكن من بيئة التشغيل
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# إعداد البوت
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# المجلد لحفظ الفيديوهات
DOWNLOADS_FOLDER = "downloads"
if not os.path.exists(DOWNLOADS_FOLDER):
    os.makedirs(DOWNLOADS_FOLDER)

# رسالة الترحيب
async def start(update: Update, context):
    await update.message.reply_text("👋 مرحبًا بك! أرسل رابط فيديو من YouTube, Facebook, Instagram وسأقوم بتحميله لك 🎥")

# تحميل الفيديو
async def download_video(update: Update, context):
    url = update.message.text

    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "instagram.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم! الرجاء إرسال رابط من YouTube أو Facebook أو Instagram.")
        return

    await update.message.reply_text("⏳ جارٍ تحميل الفيديو، يرجى الانتظار...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',  # إضافة ملفات الكوكيز لحل مشكلة تسجيل الدخول
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)  # حذف الفيديو بعد الإرسال لتوفير المساحة
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء تحميل الفيديو:\n{str(e)}")

# إضافة الأوامر
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

# تشغيل البوت
if __name__ == '__main__':
    print("✅ البوت يعمل بنجاح!")
    application.run_polling()
