import os
import threading
import time
from yt_dlp import YoutubeDL
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ==============================
# ⚙️ إعدادات عامة
# ==============================
FFMPEG_PATH = "/path/to/ffmpeg"  # تحديث المسار إلى ffmpeg
DOWNLOADS_FOLDER = "./downloads"  # مجلد التنزيلات
TOKEN = "your-telegram-bot-token"  # تحديث رمز البوت الخاص بك

# إنشاء مجلد التنزيلات إذا لم يكن موجودًا
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# ==============================
# 🎵 تنزيل الوسائط
# ==============================
def download_media_helper(url, media_type):
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
        'ffmpeg_location': FFMPEG_PATH,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'format': 'bestvideo+bestaudio/best',  # إعداد عام للوسائط
    }
    
    if media_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        })
    
    # إضافة دعم لروابط فيسبوك
    if "facebook.com" in url:
        ydl_opts['extractor_args'] = {'facebook': {'password': ''}}
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info).replace('.webm', '.mp3' if media_type == "audio" else '.mp4')
        except Exception as e:
            raise Exception(f"خطأ أثناء التنزيل: {str(e)}")

async def download_single(update, context, url, media_type):
    try:
        file_path = download_media_helper(url, media_type)
        await update.message.reply_text(f"✅ تم التنزيل بنجاح: {file_path}")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التنزيل: {str(e)}")

# ==============================
# 🤖 تشغيل البوت
# ==============================
async def start(update, context):
    chat_id = update.message.chat_id
    app.bot_data['active_chats'].add(chat_id)  # إضافة المحادثة إلى القائمة النشطة
    await update.message.reply_text("مرحبًا! استخدم /audio أو /video لتنزيل الوسائط.")

async def handle_message(update, context):
    url = update.message.text
    chat_id = update.message.chat_id
    app.bot_data['active_chats'].add(chat_id)  # إضافة المحادثة إلى القائمة النشطة
    
    if "/audio" in url:
        media_type = "audio"
    elif "/video" in url:
        media_type = "video"
    else:
        await update.message.reply_text("⚠️ الرجاء استخدام الأوامر /audio أو /video مع الرابط.")
        return
    
    # تنزيل الوسائط
    await download_single(update, context, url.split()[1], media_type)

# ==============================
# ⏳ إرسال رسائل ترحيب دورية
# ==============================
def send_periodic_messages(app):
    while True:
        time.sleep(60)  # إرسال رسالة كل دقيقة
        for chat_id in list(app.bot_data.get('active_chats', [])):
            try:
                app.bot.send_message(chat_id=chat_id, text="👋 لا تزال متصلًا بالبوت!")
            except Exception as e:
                print(f"⚠️ خطأ في إرسال الرسالة: {e}")
                app.bot_data['active_chats'].discard(chat_id)  # إزالة المحادثة غير النشطة

# ==============================
# 🌟 تشغيل البوت والمهام الدورية
# ==============================
def main():
    global app
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    # تخزين المحادثات النشطة
    app.bot_data['active_chats'] = set()

    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", lambda update, context: handle_message(update, context)))
    app.add_handler(CommandHandler("video", lambda update, context: handle_message(update, context)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل خدمة إرسال الرسائل الدورية
    threading.Thread(target=send_periodic_messages, args=(app,), daemon=True).start()
    
    print("🚀 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
