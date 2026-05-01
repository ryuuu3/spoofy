let lyricsData = null;
const lyrPanel = document.getElementById('lyr-panel');
const lyrBody = document.getElementById('lyr-body');
const lyrTitle = document.getElementById('lyr-title');
const lyrArtist = document.getElementById('lyr-artist');

document.getElementById('btn-lyrics').addEventListener('click', () => {
  lyrPanel.classList.toggle('hidden');
});
document.getElementById('btn-lyr-close').addEventListener('click', () => {
  lyrPanel.classList.add('hidden');
});

state.on('track_changed', async (track) => {
  lyrTitle.textContent = track.trackName;
  lyrArtist.textContent = track.artistName;
  lyrBody.innerHTML = '<div class="loading-spinner"></div>';
  lyricsData = null;

  try {
    const data = await api.getLyrics(track.artistName, track.trackName);
    if(data && data.syncedLyrics) {
      lyricsData = parseLrc(data.syncedLyrics);
      renderLyrics();
    } else if(data && data.plainLyrics) {
      lyrBody.innerHTML = `<div style="font-size:1rem; font-weight:normal; opacity:0.8; white-space:pre-wrap;">${data.plainLyrics}</div>`;
    } else {
      lyrBody.innerHTML = '<p class="lyr-placeholder">Lirik tidak ditemukan untuk lagu ini.</p>';
    }
  } catch(e) {
    lyrBody.innerHTML = '<p class="lyr-placeholder">Lirik tidak ditemukan.</p>';
  }
});

function parseLrc(lrc) {
  const lines = lrc.split('\n');
  const result = [];
  const regex = /\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)/;
  for(let line of lines) {
    const match = line.match(regex);
    if(match) {
      const min = parseInt(match[1]);
      const sec = parseInt(match[2]);
      const ms = parseInt(match[3]);
      const time = min * 60 + sec + (ms / (match[3].length === 2 ? 100 : 1000));
      const text = match[4].trim();
      if(text) result.push({ time, text });
    }
  }
  return result;
}

function renderLyrics() {
  if(!lyricsData) return;
  lyrBody.innerHTML = '';
  lyricsData.forEach((line, i) => {
    const el = document.createElement('div');
    el.className = 'lyr-line';
    el.id = `lyr-line-${i}`;
    el.textContent = line.text;
    el.addEventListener('click', () => {
      document.getElementById('audio-player').currentTime = line.time;
    });
    lyrBody.appendChild(el);
  });
}

let lastLineIndex = -1;
window.syncLyrics = function(time) {
  if(!lyricsData) return;
  let currentIdx = -1;
  for(let i=0; i<lyricsData.length; i++) {
    if(time >= lyricsData[i].time) currentIdx = i;
    else break;
  }
  
  if(currentIdx !== -1 && currentIdx !== lastLineIndex) {
    if(lastLineIndex !== -1) {
      const prev = document.getElementById(`lyr-line-${lastLineIndex}`);
      if(prev) prev.classList.remove('active');
    }
    const curr = document.getElementById(`lyr-line-${currentIdx}`);
    if(curr) {
      curr.classList.add('active');
      curr.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    lastLineIndex = currentIdx;
  }
}
