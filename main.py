from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx, json, uuid, os
from pathlib import Path
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI(title="Spoofy API")

# Middleware tetap perlu untuk akses dari frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ytmusic = YTMusic()

# DI VERCEL: Gunakan /tmp/ karena filesystem utama bersifat Read-Only
DATA_FILE = Path("/tmp/playlists.json")

def init_data():
    if not DATA_FILE.exists():
        # Pastikan parent folder ada (meski di /tmp biasanya langsung bisa)
        DATA_FILE.parent.mkdir(exist_ok=True)
        DATA_FILE.write_text(json.dumps({"playlists": [], "liked": []}))

def load_data():
    init_data()
    return json.loads(DATA_FILE.read_text())

def save_data(data):
    init_data()
    DATA_FILE.write_text(json.dumps(data, indent=2))

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
        'socket_timeout': 10 # Supaya tidak gantung kelamaan di Vercel
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            url = info.get('url')
            if url:
                return {"url": url}
    except Exception as e:
        print(f"Stream error: {e}")
    raise HTTPException(404, "Stream not found")

@app.get("/api/lyrics")
async def get_lyrics(artist: str, track: str, album: str = ""):
    headers = {"User-Agent": "Spoofy/1.0 (https://github.com/spoofy)"}
    async with httpx.AsyncClient() as client:
        params = {"artist_name": artist, "track_name": track}
        if album:
            params["album_name"] = album
        r = await client.get(f"{LRCLIB_BASE}/get", params=params, headers=headers)
        if r.status_code == 404:
            r2 = await client.get(f"{LRCLIB_BASE}/search", params={"q": f"{artist} {track}"}, headers=headers)
            if r2.status_code == 200 and r2.json():
                return r2.json()[0]
            raise HTTPException(404, "Lyrics not found")
        return r.json()

# -- Playlists API --
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

@app.delete("/api/playlists/{pid}")
def delete_playlist(pid: str):
    data = load_data()
    data["playlists"] = [p for p in data["playlists"] if p["id"] != pid]
    save_data(data)
    return {"ok": True}

@app.post("/api/playlists/{pid}/songs")
async def add_song(pid: str, req: Request):
    song = await req.json()
    data = load_data()
    for pl in data["playlists"]:
        if pl["id"] == pid:
            if not any(s["trackId"] == song["trackId"] for s in pl["songs"]):
                pl["songs"].append(song)
            save_data(data)
            return pl
    raise HTTPException(404, "Playlist not found")

# HAPUS app.mount static di sini, kita handle via vercel.json
