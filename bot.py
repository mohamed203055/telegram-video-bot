import os
import threading
import time
from yt_dlp import YoutubeDL
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ==============================
# ⚙️ إعدادات عامة
# ==============================
FFMPEG_PATH = "/path/to/ffmpeg"
DOWNLOADS_FOLDER = "./downloads"
TOKEN = "your-telegram-bot-token"

# ==============================
# 🎵 تنزيل الوسائط
# ==============================
def download_media_helper(url, media_type):
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
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
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3' if media_type == "audio" else '.mp4')

async def download_single(update, context, url, media_type):
    file_path = download_media_helper(url, media_type)
    await update.message.reply_text(f"✅ تم التنزيل بنجاح: {file_path}")
    return file_path

# ==============================
# 🤖 تشغيل البوت
# ==============================
async def start(update, context):
    await update.message.reply_text("مرحبًا! استخدم /audio أو /video لتنزيل الوسائط.")

async def handle_message(update, context):
    url = update.message.text
    media_type = "audio" if "/audio" in update.message.text else "video"
    await download_single(update, context, url, media_type)

# ==============================
# ⏳ إرسال رسائل ترحيب دورية
# ==============================
def send_periodic_messages(app):
    while True:
        time.sleep(60)  # إرسال رسالة كل دقيقة
        for chat_id in app.bot_data.get('active_chats', []):
            try:
                app.bot.send_message(chat_id=chat_id, text="👋 لا تزال متصلًا بالبوت!")
            except Exception as e:
                print(f"⚠️ خطأ في إرسال الرسالة: {e}")

# ==============================
# 🌟 تشغيل البوت والمهام الدورية
# ==============================
def main():
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    # تخزين المحادثات النشطة
    app.bot_data['active_chats'] = set()

    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", lambda update, context: handle_message(update, context)))
    app.add_handler(CommandHandler("video", lambda update, context: handle_message(update, context)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # إضافة المحادثة إلى القائمة النشطة عند بدء الدردشة
    async def track_chat_activity(update, context):
        chat_id = update.message.chat_id
        app.bot_data['active_chats'].add(chat_id)
    
    app.add_handler(MessageHandler(filters.ALL, track_chat_activity), group=1)
    
    # تشغيل خدمة إرسال الرسائل الدورية
    threading.Thread(target=send_periodic_messages, args=(app,), daemon=True).start()
    
    print("🚀 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
