const audio = document.getElementById('audio-player');
const playBtn = document.getElementById('btn-play');
const playIcon = document.getElementById('play-icon');
const pauseIcon = document.getElementById('pause-icon');
const progTrack = document.getElementById('prog-track');
const progFill = document.getElementById('prog-fill');
const curTimeEl = document.getElementById('pb-cur');
const durTimeEl = document.getElementById('pb-dur');
const volSlider = document.getElementById('vol-slider');

function formatTime(ms) {
  if(!ms || isNaN(ms)) return "0:00";
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

state.on('track_changed', async (track) => {
  document.getElementById('pb-track').textContent = track.trackName;
  document.getElementById('pb-artist').textContent = track.artistName;
  
  const img = document.getElementById('pb-art-img');
  const emoji = document.getElementById('pb-art-emoji');
  if(track.artworkUrl100) {
    img.src = track.artworkUrl100;
    img.style.display = 'block';
    emoji.style.display = 'none';
  } else {
    img.style.display = 'none';
    emoji.style.display = 'block';
  }

  // Check liked
  const isLiked = state.likedSongs.some(s => s.trackId === track.trackId);
  document.getElementById('pb-like').style.color = isLiked ? 'var(--brand)' : 'var(--text-secondary)';

  durTimeEl.textContent = formatTime(track.trackTimeMillis || 0);

  // Fetch Stream URL
  const url = await api.getStreamUrl(track.trackId);
  if(url) {
    audio.src = url;
    audio.play();
  } else {
    alert("Audio stream not found for this track.");
    state.togglePlay();
  }
});

state.on('play_toggled', (isPlaying) => {
  if(isPlaying) {
    audio.play();
    playIcon.classList.add('hidden');
    pauseIcon.classList.remove('hidden');
  } else {
    audio.pause();
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
  }
});

playBtn.addEventListener('click', () => state.togglePlay());
document.getElementById('btn-next').addEventListener('click', () => state.nextTrack());
document.getElementById('btn-prev').addEventListener('click', () => state.prevTrack());

audio.addEventListener('timeupdate', () => {
  if(!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  progFill.style.width = `${pct}%`;
  curTimeEl.textContent = formatTime(audio.currentTime * 1000);
  
  // Sync lyrics if open
  if(window.syncLyrics) window.syncLyrics(audio.currentTime);
});

audio.addEventListener('ended', () => {
  state.nextTrack();
});

audio.addEventListener('play', () => {
  state.isPlaying = true;
  playIcon.classList.add('hidden');
  pauseIcon.classList.remove('hidden');
});
audio.addEventListener('pause', () => {
  state.isPlaying = false;
  playIcon.classList.remove('hidden');
  pauseIcon.classList.add('hidden');
});

progTrack.addEventListener('click', (e) => {
  if(!audio.duration) return;
  const rect = progTrack.getBoundingClientRect();
  const pct = (e.clientX - rect.left) / rect.width;
  audio.currentTime = pct * audio.duration;
});

volSlider.addEventListener('input', (e) => {
  audio.volume = e.target.value / 100;
});
audio.volume = volSlider.value / 100;
