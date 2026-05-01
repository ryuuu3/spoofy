from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx, json, uuid, os
from pathlib import Path
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI(title="Spoofy API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ytmusic = YTMusic()

# --- PERBAIKAN KRITIS UNTUK VERCEL ---
# Di Vercel, kita hanya boleh menulis di folder /tmp/
DATA_FILE = Path("/tmp/playlists.json")

def load_data():
    if not DATA_FILE.exists():
        # Inisialisasi data kosong jika file belum ada di /tmp/
        return {"playlists": [], "liked": []}
    try:
        return json.loads(DATA_FILE.read_text())
    except:
        return {"playlists": [], "liked": []}

def save_data(data):
    # Simpan ke folder /tmp/ yang diizinkan Vercel
    DATA_FILE.write_text(json.dumps(data, indent=2))
# --------------------------------------

LRCLIB_BASE = "https://lrclib.net/api"

def parse_yt_duration(duration_str):
    if not duration_str: return 0
    parts = duration_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

@app.get("/api/search")
async def search(q: str):
    results = ytmusic.search(q, filter="songs", limit=20)
    formatted = []
    for r in results:
        artist_name = r['artists'][0]['name'] if r.get('artists') else "Unknown"
        album_name = r['album']['name'] if r.get('album') else ""
        art_url = r['thumbnails'][-1]['url'] if r.get('thumbnails') else ""
        dur = parse_yt_duration(r.get('duration'))
        formatted.append({
            "trackId": r['videoId'],
            "trackName": r['title'],
            "artistName": artist_name,
            "albumName": album_name,
            "artworkUrl100": art_url,
            "trackTimeMillis": dur * 1000
        })
    return {"results": formatted}

@app.get("/api/trending")
async def trending():
    charts = ytmusic.get_charts(country='ID')
    formatted = []
    songs = charts.get('trending', {}).get('items', [])
    if not songs:
        songs = charts.get('tracks', {}).get('items', [])
    
    for r in songs[:20]:
        artist_name = r['artists'][0]['name'] if r.get('artists') else "Unknown"
        album_name = r['album']['name'] if r.get('album') else ""
        art_url = r['thumbnails'][-1]['url'] if r.get('thumbnails') else ""
        dur = 0 
        formatted.append({
            "trackId": r['videoId'],
            "trackName": r['title'],
            "artistName": artist_name,
            "albumName": album_name,
            "artworkUrl100": art_url,
            "trackTimeMillis": dur * 1000
        })
    return {"results": formatted}

@app.get("/api/stream/{video_id}")
async def get_stream(video_id: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': False,
        'cachedir': '/tmp/yt-dlp-cache' # Pastikan cache juga ke /tmp/
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            url = info.get('url')
            if url:
                return {"url": url}
    except Exception as e:
        print(f"Error streaming: {e}")
    raise HTTPException(404, "Stream not found")

@app.get("/api/lyrics")
async def get_lyrics(artist: str, track: str, album: str = ""):
    headers = {"User-Agent": "Spoofy/1.0"}
    async with httpx.AsyncClient() as client:
        params = {"artist_name": artist, "track_name": track}
        if album: params["album_name"] = album
        r = await client.get(f"{LRCLIB_BASE}/get", params=params, headers=headers)
        if r.status_code == 404:
            r2 = await client.get(f"{LRCLIB_BASE}/search", params={"q": f"{artist} {track}"}, headers=headers)
            if r2.status_code == 200 and r2.json():
                return r2.json()[0]
            raise HTTPException(404, "Lyrics not found")
        return r.json()

# --- Playlists & Liked (Menggunakan fungsi load/save baru) ---
@app.get("/api/playlists")
def list_playlists():
    return load_data()["playlists"]

@app.post("/api/playlists")
async def create_playlist(req: Request):
    body = await req.json()
    data = load_data()
    pl = {"id": str(uuid.uuid4()), "name": body.get("name","New Playlist"),
          "desc": body.get("desc",""), "emoji": body.get("emoji","🎵"), "songs": []}
    data["playlists"].append(pl)
    save_data(data)
    return pl

@app.get("/api/liked")
def get_liked():
    return load_data()["liked"]

@app.post("/api/liked")
async def like_song(req: Request):
    song = await req.json()
    data = load_data()
    if not any(s["trackId"] == song["trackId"] for s in data["liked"]):
        data["liked"].append(song)
        save_data(data)
    return data["liked"]

# Tetap mount statis di akhir
app.mount("/", StaticFiles(directory="static", html=True), name="static")
