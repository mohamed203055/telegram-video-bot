import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# تفعيل تسجيل الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# استدعاء توكن البوت من البيئة
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# مسار ملف الكوكيز لحل مشكلة تسجيل الدخول
COOKIES_FILE = "cookies.txt"

def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رسالة الترحيب عند بدء المحادثة."""
    update.message.reply_text("مرحبًا! أرسل رابط الفيديو لاختيار نوع التحميل 🎯")

def choose_download_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال قائمة للاختيار بين تحميل الصوت أو الفيديو."""
    url = update.message.text
    keyboard = [[
        InlineKeyboardButton("🎵 تحميل الصوت", callback_data=f"audio|{url}"),
        InlineKeyboardButton("📹 تحميل الفيديو", callback_data=f"video|{url}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر نوع التحميل ⬇", reply_markup=reply_markup)

def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تنزيل الوسائط حسب اختيار المستخدم."""
    query = update.callback_query
    await query.answer()
    choice, url = query.data.split('|')
    
    query.edit_message_text(text="⏳ جارٍ التحميل... الرجاء الانتظار.")
    
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'outtmpl': '%(title)s.%(ext)s',
        'cookiefile': COOKIES_FILE,  # استخدام الكوكيز لحل مشكلة تسجيل الدخول
    }
    
    if choice == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            if choice == "audio":
                file_name = file_name.replace(".webm", ".mp3").replace(".m4a", ".mp3")
        
        query.message.reply_text("✅ تم التحميل! جارٍ الإرسال...")
        with open(file_name, 'rb') as file:
            if choice == "audio":
                await query.message.reply_audio(file)
            else:
                await query.message.reply_video(file)
        os.remove(file_name)
    except Exception as e:
        query.message.reply_text(f"❌ حدث خطأ أثناء التحميل:\n{e}")

# إعداد البوت
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choose_download_type))
app.add_handler(CallbackQueryHandler(download_media))

# تشغيل البوت
if __name__ == "__main__":
    print("✅ البوت يعمل بنجاح!")
    app.run_polling()}
