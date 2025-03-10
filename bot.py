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
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(DOWNLOADS_FOLDER, info.get('playlist_title', 'playlist'))

async def download_single(url, media_type):
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_FOLDER}/%(title)s.%(ext)s',
        'ffmpeg_location': FFMPEG_PATH,
        'nocheckcertificate': True,
    }
    
    if media_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3' if media_type == "audio" else '.mp4')

# ================================================
# 🤖 تشغيل البوت مع إدارة أفضل للموارد
# ================================================
def main():
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", download_media))
    app.add_handler(CommandHandler("video", download_media))
    app.add_handler(CommandHandler("album", download_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل خدمة الخلفية لإبقاء البوت نشطًا
    threading.Thread(target=keep_alive, daemon=True).start()
    
    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

# ================================================
# 🌍 خادم ويب محسن
# ================================================
flask_app = Flask(name)
@flask_app.route('/')
def home():
    return "✅ البوت يعمل بشكل طبيعي!"

def keep_alive():
    flask_app.run(host='0.0.0.0', port=8080)

if name == "main":
    main()
