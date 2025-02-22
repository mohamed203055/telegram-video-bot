import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# إعداد تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب توكن البوت من المتغيرات البيئية
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# حفظ لغة المستخدم
user_languages = {}

def start(update: Update, context):
    """عند بدء البوت، يطلب من المستخدم اختيار اللغة"""
    keyboard = [[InlineKeyboardButton("العربية 🇸🇦", callback_data='lang_ar'),
                 InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر لغتك:\nChoose your language:", reply_markup=reply_markup)

def language_selection(update: Update, context):
    """حفظ لغة المستخدم بعد الاختيار"""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    
    if query.data == 'lang_ar':
        user_languages[chat_id] = 'ar'
        query.edit_message_text("✅ اللغة المختارة: العربية")
    else:
        user_languages[chat_id] = 'en'
        query.edit_message_text("✅ Selected language: English")
    
    show_download_options(query, chat_id)

def show_download_options(update, chat_id):
    """عرض خيارات تحميل الفيديو أو الصوت"""
    lang = user_languages.get(chat_id, 'en')
    
    text = "اختر نوع التحميل 🎯:" if lang == 'ar' else "Choose download type 🎯:"
    keyboard = [[InlineKeyboardButton("🎵 تحميل الصوت", callback_data='audio'),
                 InlineKeyboardButton("📹 تحميل الفيديو", callback_data='video')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text, reply_markup=reply_markup)

def handle_download(update: Update, context):
    """استقبال رابط الفيديو من المستخدم"""
    chat_id = update.message.chat_id
    user_languages.setdefault(chat_id, 'en')  # تعيين لغة افتراضية
    
    context.user_data['url'] = update.message.text  # حفظ الرابط
    show_download_options(update, chat_id)

def process_download(update: Update, context):
    """بدء عملية تحميل الفيديو أو الصوت"""
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    choice = query.data
    
    url = context.user_data.get('url')
    if not url:
        query.edit_message_text("❌ يرجى إرسال رابط فيديو أولاً!" if user_languages[chat_id] == 'ar' else "❌ Please send a video link first!")
        return
    
    query.edit_message_text("⏳ جارٍ تحميل الملف..." if user_languages[chat_id] == 'ar' else "⏳ Downloading the file...")
    
    file_path = download_media(url, choice)
    if file_path:
        context.bot.send_document(chat_id, open(file_path, 'rb'))
        os.remove(file_path)
    else:
        query.edit_message_text("❌ فشل التحميل!" if user_languages[chat_id] == 'ar' else "❌ Download failed!")

def download_media(url, choice):
    """تحميل الفيديو أو الصوت باستخدام yt-dlp مع دعم ملفات الكوكيز"""
    output_template = f"{DOWNLOADS_FOLDER}/%(title)s.%(ext)s"
    
    options = {
        'format': 'bestaudio/best' if choice == "audio" else 'best',
        'outtmpl': output_template,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if choice == "audio" else [],
        'cookies': 'cookies.txt'  # استخدام ملف الكوكيز المصادق عليه
    }
    
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return file_path.replace(".webm", ".mp3") if choice == "audio" else file_path
    except Exception as e:
        logger.error(f"❌ خطأ أثناء التحميل: {e}")
        return None

# تشغيل البوت
if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
    app.add_handler(CallbackQueryHandler(language_selection, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(process_download, pattern="^(audio|video)$"))
    
    app.run_polling()
