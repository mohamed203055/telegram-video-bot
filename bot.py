import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# الحصول على التوكن من بيئة التشغيل
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# إعداد البوت
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# المجلد لحفظ الملفات
DOWNLOADS_FOLDER = "downloads"
if not os.path.exists(DOWNLOADS_FOLDER):
    os.makedirs(DOWNLOADS_FOLDER)

# حفظ الروابط الواردة مؤقتًا
user_links = {}

# رسالة الترحيب
async def start(update: Update, context):
    await update.message.reply_text("👋 مرحبًا بك! أرسل رابط فيديو من YouTube, Facebook, Instagram وسأقوم بتحميله لك 🎥")

# استقبال الرابط وإظهار قائمة الاختيار
async def receive_link(update: Update, context):
    url = update.message.text

    if not any(site in url for site in ["youtube.com", "youtu.be", "facebook.com", "instagram.com"]):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم! الرجاء إرسال رابط من YouTube أو Facebook أو Instagram.")
        return

    # حفظ الرابط في ذاكرة المستخدم
    user_links[update.message.chat_id] = url

    # إنشاء أزرار الاختيار
    keyboard = [
        [InlineKeyboardButton("🎵 تحميل الصوت", callback_data="audio")],
        [InlineKeyboardButton("🎥 تحميل الفيديو", callback_data="video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("🎯 اختر نوع التحميل:", reply_markup=reply_markup)

# تحميل الفيديو أو الصوت بناءً على الاختيار
async def download_media(update: Update, context):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    url = user_links.get(chat_id, None)

    if not url:
        await query.message.reply_text("❌ لم أتمكن من العثور على الرابط. أرسل الرابط من جديد.")
        return

    # إعداد الخيارات بناءً على الاختيار
    if query.data == "audio":
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': 'cookies.txt',
        }
        file_type = "الصوت"
    else:
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
            'cookiefile': 'cookies.txt',
        }
        file_type = "الفيديو"

    await query.message.reply_text(f"⏳ جارٍ تحميل {file_type}، يرجى الانتظار...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if query.data == "audio":
            file_path = file_path.rsplit('.', 1)[0] + ".mp3"

        await query.message.reply_document(document=open(file_path, 'rb'))
        os.remove(file_path)  # حذف الملف بعد الإرسال لتوفير المساحة
    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ أثناء تحميل {file_type}:\n{str(e)}")

# إضافة الأوامر
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
application.add_handler(CallbackQueryHandler(download_media))

# تشغيل البوت
if __name__ == '__main__':
    print("✅ البوت يعمل بنجاح!")
    application.run_polling()
