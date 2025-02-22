async def download_media(url, choice):
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
