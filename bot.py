from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp
import os

# استخدام المتغير البيئي لحماية التوكن
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("👋 مرحبًا! أرسل لي رابط فيديو وسأقوم بتحميله لك 🎥")

async def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text

    if "youtube.com" in url or "youtu.be" in url or "facebook.com" in url or "instagram.com" in url:
        await update.message.reply_text("⏳ جاري تحميل الفيديو، يرجى الانتظار...")

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)

    else:
        await update.message.reply_text("❌ هذا الرابط غير مدعوم!")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    application.run_polling()

if __name__ == '__main__':
    main()
