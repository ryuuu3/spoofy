from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx, json, uuid
from pathlib import Path
from ytmusicapi import YTMusic

app = FastAPI(title="Spoofy API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ytmusic = YTMusic()
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

@app.get("/api/stream/{video_id}")
async def get_stream(video_id: str):
    url_yt = f"https://www.youtube.com/watch?v={video_id}"
    
    # Menggunakan instance alternatif (ghst) yang tidak butuh JWT/API Key
    instance_url = "https://cobalt.api.ghst.xyz/"
    
    async with httpx.AsyncClient(timeout=25.0) as client:
        try:
            response = await client.post(
                instance_url,
                json={
                    "url": url_yt,
                    "downloadMode": "audio",
                    "audioFormat": "mp3"
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("url"):
                    return {"url": data.get("url")}
            
            print(f"Cobalt Status: {response.status_code}")
        except Exception as e:
            print(f"Stream Error: {str(e)}")
    
    raise HTTPException(status_code=404, detail="Gagal mengambil audio.")

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
    body, data = await req.json(), load_data()
    pl = {"id": str(uuid.uuid4()), "name": body.get("name","New Playlist"), "songs": []}
    data["playlists"].append(pl)
    save_data(data)
    return pl

@app.get("/api/liked")
def get_liked(): 
    return load_data()["liked"]

@app.post("/api/liked")
async def like_song(req: Request):
    song, data = await req.json(), load_data()
    if not any(s["trackId"] == song["trackId"] for s in data["liked"]):
        data["liked"].append(song)
        save_data(data)
    return data["liked"]

# Melayani file statis
app.mount("/", StaticFiles(directory="static", html=True), name="static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
