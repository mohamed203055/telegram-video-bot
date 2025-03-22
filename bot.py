from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import yt_dlp  # بدلًا من youtube_dl
import os
import logging

# تفعيل التسجيل لاكتشاف الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# التوكن الخاص بالبوت (غيّره إلى توكنك)
TOKEN = 'YOUR_BOT_TOKEN'

# إعداد خيارات التحميل مع دعم الجودات المختلفة
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'playliststart': 1,  # لدعم قوائم التشغيل
    'playlistend': 10,   # عدد المقاطع من الألبوم (10 كحد أقصى)
}

# معالجة الأمر /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحبًا! أرسل رابط الفيديو أو الألبوم.\n\n'
                             'البوت يدعم: يوتيوب، فيسبوك، إنستجرام، وروابط الفيديو المباشرة.')

# معالجة الروابط الواردة
def handle_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    
    # إنشاء لوحة المفاتيح مع خيارات التحميل
    keyboard = [
        [
            InlineKeyboardButton("صوت", callback_data=f'audio_128_{url}'),
            InlineKeyboardButton("صوت عالي", callback_data=f'audio_320_{url}')
        ],
        [
            InlineKeyboardButton("فيديو 720p", callback_data=f'video_720_{url}'),
            InlineKeyboardButton("فيديو 1080p", callback_data=f'video_1080_{url}')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('اختر نوع وجودة التحميل:', reply_markup=reply_markup)

# معالجة اختيار النوع والجودة
def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # فصل البيانات من callback_data
    data = query.data.split('_')
    media_type = data[0]
    quality = data[1]
    url = '_'.join(data[2:])  # لدعم الروابط التي تحتوي على شرطات
    
    # تعديل خيارات التحميل بناءً على الاختيار
    if media_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'][0]['preferredquality'] = quality
    else:
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # استخراج معلومات الملف/الألبوم
            info = ydl.extract_info(url, download=False)
            
            # إذا كان الرابط ألبومًا (قائمة تشغيل)
            if 'entries' in info:
                query.edit_message_text('جارٍ تحميل الألبوم...')
                for entry in info['entries']:
                    download_and_send(query, entry, media_type, context)
            else:
                download_and_send(query, info, media_type, context)
                
    except Exception as e:
        query.edit_message_text(f'حدث خطأ: {str(e)}')

# دالة مساعدة للتحميل والإرسال
def download_and_send(query, info, media_type, context):
    title = info.get('title', 'الملف')
    filename = f"downloads/{title}.{media_type if media_type == 'video' else 'mp3'}"
    
    # بدء التحميل
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([info['webpage_url']])
    
    # إرسال الملف للمستخدم
    try:
        if media_type == 'audio':
            with open(filename, 'rb') as audio_file:
                context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=audio_file,
                    title=title,
                    caption=f'🎧 {title}'
                )
        else:
            with open(filename, 'rb') as video_file:
                context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption=f'🎬 {title}'
                )
    except Exception as e:
        query.message.reply_text(f"خطأ في إرسال الملف: {str(e)}")
    
    # حذف الملف بعد الإرسال
    if os.path.exists(filename):
        os.remove(filename)

# إعداد الـ Handlers
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# إضافة معالجات الأوامر
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.regex(r'https?://'), handle_url))
dispatcher.add_handler(CallbackQueryHandler(button_click))

# تشغيل البوت
if __name__ == '__main__':
    # إنشاء مجلد التحميلات إذا لم يوجد
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    updater.start_polling()
    updater.idle()
