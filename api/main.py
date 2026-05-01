from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx, json, uuid, os
from pathlib import Path
from ytmusicapi import YTMusic

app = FastAPI(title="Spoofy API")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ytmusic = YTMusic()

# --- KONFIGURASI PENYIMPANAN VERCEL ---
# Menggunakan /tmp/ karena sistem file Vercel bersifat read-only
DATA_FILE = Path("/tmp/playlists.json")

def load_data():
    if not DATA_FILE.exists():
        return {"playlists": [], "liked": []}
    try:
        return json.loads(DATA_FILE.read_text())
    except:
        return {"playlists": [], "liked": []}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

# --- BYPASS STREAMING (COBALT API) ---
@app.get("/api/stream/{video_id}")
async def get_stream(video_id: str):
    """
    Mengambil URL stream audio menggunakan Cobalt API untuk menghindari 
    deteksi bot YouTube yang memblokir IP server Vercel.
    """
    url_yt = f"https://www.youtube.com/watch?v={video_id}"
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            # Menggunakan instance publik Cobalt yang stabil
            response = await client.post(
                "https://api.cobalt.tools/api/json",
                json={
                    "url": url_yt,
                    "downloadMode": "audio",
                    "audioFormat": "mp3",
                    "isNoTTWatermark": True
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("url"):
                    return {"url": data["url"]}
                
            print(f"Cobalt Error: {response.text}")
        except Exception as e:
            print(f"Streaming Exception: {e}")
    
    raise HTTPException(status_code=404, detail="Audio stream blocked by YouTube.")

# --- FITUR PENCARIAN & TRENDING ---
@app.get("/api/search")
async def search(q: str):
    results = ytmusic.search(q, filter="songs", limit=20)
    formatted = []
    for r in results:
        artist_name = r['artists'][0]['name'] if r.get('artists') else "Unknown"
        art_url = r['thumbnails'][-1]['url'] if r.get('thumbnails') else ""
        formatted.append({
            "trackId": r['videoId'],
            "trackName": r['title'],
            "artistName": artist_name,
            "albumName": r.get('album', {}).get('name', ""),
            "artworkUrl100": art_url,
            "trackTimeMillis": 0
        })
    return {"results": formatted}

@app.get("/api/trending")
async def trending():
    charts = ytmusic.get_charts(country='ID')
    songs = charts.get('trending', {}).get('items', []) or charts.get('tracks', {}).get('items', [])
    formatted = []
    for r in songs[:20]:
        artist_name = r['artists'][0]['name'] if r.get('artists') else "Unknown"
        art_url = r['thumbnails'][-1]['url'] if r.get('thumbnails') else ""
        formatted.append({
            "trackId": r['videoId'],
            "trackName": r['title'],
            "artistName": artist_name,
            "artworkUrl100": art_url
        })
    return {"results": formatted}

# --- LIRIK & DATA USER ---
@app.get("/api/lyrics")
async def get_lyrics(artist: str, track: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://lrclib.net/api/get?artist_name={artist}&track_name={track}")
        if r.status_code == 200:
            return r.json()
        return {"error": "Lyrics not found"}

@app.get("/api/playlists")
def list_playlists(): 
    return load_data()["playlists"]

@app.post("/api/playlists")
async def create_playlist(req: Request):
    body = await req.json()
    data = load_data()
    pl = {"id": str(uuid.uuid4()), "name": body.get("name","New Playlist"), "songs": []}
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

# Melayani file statis
app.mount("/", StaticFiles(directory="static", html=True), name="static")
