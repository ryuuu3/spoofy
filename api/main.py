from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx, json, uuid, logging
from pathlib import Path
from ytmusicapi import YTMusic

# Matikan logger internal yang sering bikin "Device Busy" di Vercel
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ytmusic = YTMusic()
# Gunakan memori saja untuk storage jika /tmp/ bermasalah
STORAGE = {"playlists": [], "liked": []}

@app.get("/api/stream/{video_id}")
async def get_stream(video_id: str):
    # Gunakan instance kencang yang jarang overload
    url_yt = f"https://www.youtube.com/watch?v={video_id}"
    instance = "https://cobalt.api.ghst.xyz/"
    
    # Force close connection setelah selesai
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            resp = await client.post(
                instance,
                json={"url": url_yt, "downloadMode": "audio", "audioFormat": "mp3"},
                headers={"Accept": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if "url" in data:
                    return {"url": data["url"]}
        except Exception as e:
            print(f"S: {str(e)}")
            
    raise HTTPException(status_code=404, detail="Busy")

@app.get("/api/search")
async def search(q: str):
    search_results = ytmusic.search(q, filter="songs", limit=15)
    formatted = []
    for r in search_results:
        formatted.append({
            "trackId": r['videoId'],
            "trackName": r['title'],
            "artistName": r['artists'][0]['name'] if r.get('artists') else "Unknown",
            "artworkUrl100": r['thumbnails'][-1]['url'] if r.get('thumbnails') else ""
        })
    return {"results": formatted}

@app.get("/api/trending")
async def trending():
    charts = ytmusic.get_charts(country='ID')
    songs = charts.get('trending', {}).get('items', [])[:20]
    formatted = []
    for r in songs:
        formatted.append({
            "trackId": r['videoId'],
            "trackName": r['title'],
            "artistName": r['artists'][0]['name'] if r.get('artists') else "Unknown",
            "artworkUrl100": r['thumbnails'][-1]['url'] if r.get('thumbnails') else ""
        })
    return {"results": formatted}

@app.get("/api/lyrics")
async def get_lyrics(artist: str, track: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"https://lrclib.net/api/get?artist_name={artist}&track_name={track}")
        return r.json() if r.status_code == 200 else {"error": "None"}

@app.get("/api/playlists")
def list_pl(): return STORAGE["playlists"]

@app.post("/api/playlists")
async def create_pl(req: Request):
    body = await req.json()
    pl = {"id": str(uuid.uuid4()), "name": body.get("name", "New"), "songs": []}
    STORAGE["playlists"].append(pl)
    return pl

@app.get("/api/liked")
def get_liked(): return STORAGE["liked"]

@app.post("/api/liked")
async def like(req: Request):
    song = await req.json()
    if not any(s["trackId"] == song["trackId"] for s in STORAGE["liked"]):
        STORAGE["liked"].append(song)
    return STORAGE["liked"]

app.mount("/", StaticFiles(directory="static", html=True), name="static")
