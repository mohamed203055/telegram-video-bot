import telebot
import yt_dlp
import os
import threading

# 🔹 ضع توكن البوت هنا
BOT_TOKEN = "YOUR_BOT_TOKEN"

bot = telebot.TeleBot(BOT_TOKEN)

# 🔹 مجلد التخزين المؤقت للمقاطع
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 🔹 دالة تحميل الصوتيات
def download_audio(url, chat_id, message_id):
    try:
        bot.edit_message_text("⏳ جاري تحليل الرابط...", chat_id, message_id)

        # إعدادات yt-dlp لتنزيل الصوتيات فقط
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(playlist_index)s - %(title)s.%(ext)s',  
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': False,  # فرض تحميل قائمة التشغيل
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # إذا كان الرابط لقائمة تشغيل
            if 'entries' in info:
                total_videos = len(info['entries'])
                bot.edit_message_text(f"📥 جاري تحميل {total_videos} مقطع صوتي بالترتيب...", chat_id, message_id)

                for entry in sorted(info['entries'], key=lambda x: x['playlist_index']):
                    file_path = f"{DOWNLOAD_FOLDER}/{entry['playlist_index']} - {entry['title']}.mp3"
                    send_audio(file_path, chat_id)

            else:  # إذا كان الرابط لفيديو واحد فقط
                file_path = f"{DOWNLOAD_FOLDER}/{info['title']}.mp3"
                bot.edit_message_text("📥 جاري تحميل مقطع واحد...", chat_id, message_id)
                send_audio(file_path, chat_id)

        bot.send_message(chat_id, "✅ تم تحميل جميع المقاطع الصوتية!")

    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}")

# 🔹 دالة إرسال الملفات الصوتية وحذفها بعد الإرسال
def send_audio(file_path, chat_id):
    try:
        with open(file_path, 'rb') as audio:
            bot.send_audio(chat_id, audio)
        os.remove(file_path)  # حذف الملف بعد الإرسال
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ خطأ أثناء إرسال الملف: {str(e)}")

# 🔹 رسالة الترحيب
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 مرحبًا بك!\nأرسل لي رابط **فيديو يوتيوب أو قائمة تشغيل**، وسأقوم باستخراج جميع الصوتيات لك! 🎵")

# 🔹 التعامل مع الروابط (يدعم الفيديوهات الفردية وقوائم التشغيل)
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_url(message):
    msg = bot.send_message(message.chat.id, "🔍 جاري التحقق من الرابط...")
    
    # تشغيل التحميل في خيط منفصل (Thread) لمنع تجميد البوت
    threading.Thread(target=download_audio, args=(message.text, message.chat.id, msg.message_id)).start()

# 🔹 تشغيل البوت
bot.polling()
