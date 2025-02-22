import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# الحصول على التوكن من المتغير البيئي
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# إعداد السجل لتتبع الأخطاء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مجلد التنزيلات
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

async def start(update: Update, context):
    """رسالة الترحيب عند تشغيل البوت"""
    keyboard = [
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 Please choose your language / يرجى اختيار اللغة", reply_markup=reply_markup)

async def language_choice(update: Update, context):
    """معالجة اختيار اللغة"""
    query = update.callback_query
    await query.answer()

    language = query.data
    context.user_data['language'] = language

    if language == "lang_ar":
        await query.edit_message_text("مرحبًا! أرسل رابط فيديو وسأساعدك في تحميله 🎥🎵")
    elif language == "lang_en":
        await query.edit_message_text("Hello! Send a video link, and I'll help you download it 🎥🎵")

async def download_menu(update: Update, context):
    """إظهار قائمة التحميل عند إرسال رابط"""
    url = update.message.text
    keyboard = [
        [InlineKeyboardButton("🎵 تحميل الصوت (MP3)", callback_data=f"audio|{url}")],
        [InlineKeyboardButton("📹 تحميل الفيديو (MP4)", callback_data=f"video|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    language = context.user_data.get('language', 'lang_en')
    message_text = "🎯 اختر نوع التحميل:" if language == 'lang_ar' else "🎯 Choose the type of download:"
    
    await update.message.reply_text(message_text, reply_markup=reply_markup)

async def button_handler(update: Update, context):
    """معالجة زر الاختيار وتنفيذ التحميل"""
    query = update.callback_query
    await query.answer()

    choice, url = query.data.split("|")
    chat_id = query.message.chat_id

    await query.edit_message_text("⏳ جارٍ التحميل، يرجى الانتظار...")

    file_path = await download_media(url, choice)

    if file_path:
        await context.bot.send_document(chat_id, document=open(file_path, "rb"))
        os.remove(file_path)  # حذف الملف بعد الإرسال
    else:
        await query.edit_message_text("❌ حدث خطأ أثناء التحميل.")

async def download_media(url, choice):
    """تحميل الفيديو أو الصوت باستخدام yt-dlp مع دعم cookies.txt"""
    output_template = f"{DOWNLOADS_FOLDER}/%(title)s.%(ext)s"
    options = {
        'format': 'bestaudio/best' if choice == "audio" else 'best',
        'outtmpl': output_template,
        'ffmpeg_location': "/usr/bin/ffmpeg",  # تأكد من تثبيت FFmpeg
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if choice == "audio" else []
    }

    # إضافة `cookies.txt` إذا كان موجودًا
    if os.path.exists("cookies.txt"):
        options['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return file_path.replace(".webm", ".mp3") if choice == "audio" else file_path
    except Exception as e:
        logger.error(f"❌ خطأ أثناء التحميل: {e}")
        return None

def main():
    """تشغيل البوت"""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_menu))
    app.add_handler(CallbackQueryHandler(language_choice, pattern="^(lang_ar|lang_en)$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
