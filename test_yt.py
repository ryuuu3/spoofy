import yt_dlp
import json

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extract_flat': False
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info("ytsearch1:shape of you ed sheeran", download=False)
    if 'entries' in info and len(info['entries']) > 0:
        entry = info['entries'][0]
        print(f"Title: {entry.get('title')}")
        print(f"URL: {entry.get('url')}")
