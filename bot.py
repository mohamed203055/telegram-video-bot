# حفظ هذا الملف كـ bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import youtube_dl

# التوكن الذي حصلت عليه من BotFather
TOKEN = 'YOUR_BOT_TOKEN'

# إعداد خيارات التحميل
ydl_opts = {
    'format': 'bestaudio/best',  # التحميل كصوت افتراضيًا
    'outtmpl': '%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

# معالجة الأمر /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحبًا! أرسل رابط الفيديو أو الألبوم.')

# معالجة الروابط الواردة
def handle_url(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    keyboard = [
        [InlineKeyboardButton("صوت", callback_data=f'audio_{url}')],
        [InlineKeyboardButton("فيديو", callback_data=f'video_{url}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('اختر نوع التحميل:', reply_markup=reply_markup)

# معالجة اختيار النوع (صوت/فيديو)
def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    type, url = query.data.split('_', 1)
    
    if type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'الملف')
        query.edit_message_text(f'جارٍ تحميل: {title}...')
        
        # بدء التحميل
        ydl.download([url])
    
    # إرسال الملف للمستخدم
    context.bot.send_audio(
        chat_id=query.message.chat_id,
        audio=open(f'{title}.mp3', 'rb') if type == 'audio' else open(f'{title}.mp4', 'rb')
    )

# إعداد الـ Handlers
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.regex(r'http'), handle_url))
dispatcher.add_handler(CallbackQueryHandler(button_click))

# تشغيل البوت
updater.start_polling()
updater.idle()
