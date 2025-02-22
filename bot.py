from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp
import os

# استخدام المتغير البيئي لحماية التوكن
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 مرحبًا! أرسل لي رابط فيديو وسأقوم بتحميله لك 🎥")

def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text

    if "youtube.com" in url or "youtu.be" in url or "facebook.com" in url or "instagram.com" in url:
        update.message.reply_text("⏳ جاري تحميل الفيديو، يرجى الانتظار...")

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)

    else:
        update.message.reply_text("❌ هذا الرابط غير مدعوم!")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
