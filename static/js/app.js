const mainContent = document.getElementById('main-content');
let currentView = 'home';

// INIT
async function init() {
  if(!state.user.name) {
    document.getElementById('m-auth').classList.remove('hidden');
  } else {
    showApp();
  }
  
  // load data
  const pls = await api.getPlaylists();
  state.setPlaylists(pls);
  const liked = await api.getLiked();
  state.setLiked(liked);
  
  document.getElementById('pb-like').addEventListener('click', async () => {
    if(!state.currentTrack) return;
    const isLiked = state.likedSongs.some(s => s.trackId === state.currentTrack.trackId);
    const updated = await api.toggleLike(state.currentTrack, isLiked);
    if(updated) state.setLiked(updated);
  });
}

function showApp() {
  document.getElementById('landing-page').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('s-uname').textContent = state.user.name;
  document.getElementById('s-avatar').textContent = state.user.name.charAt(0).toUpperCase();
  renderView(currentView);
}

// ROUTING
document.querySelectorAll('.snav-item').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('.snav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    currentView = el.dataset.view;
    renderView(currentView);
  });
});

async function renderView(view, param = null) {
  mainContent.innerHTML = '<div class="loading-spinner"></div>';
  
  if(view === 'home') {
    const res = await api.trending();
    mainContent.innerHTML = `
      <div class="view-container">
        <div class="view-header"><h1 class="view-title">Good Evening, ${state.user.name}</h1></div>
        <h2>Trending Now</h2>
        <div class="grid-container" id="home-grid"></div>
      </div>
    `;
    renderGrid('home-grid', res.results, res.results);
  } 
  else if(view === 'search') {
    mainContent.innerHTML = `
      <div class="search-bar-wrap">
        <input type="text" id="inp-search" class="search-input" placeholder="Apa yang ingin kamu dengarkan?" autocomplete="off"/>
      </div>
      <div class="view-container">
        <div id="search-results" class="track-list">
          <p style="color:var(--text-secondary)">Ketik sesuatu untuk mulai mencari.</p>
        </div>
      </div>
    `;
    let timeout = null;
    document.getElementById('inp-search').addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(async () => {
        const q = e.target.value.trim();
        if(q.length < 2) return;
        document.getElementById('search-results').innerHTML = '<div class="loading-spinner"></div>';
        const res = await api.search(q);
        renderTrackList('search-results', res.results, res.results);
      }, 500);
    });
  }
  else if(view === 'library') {
    mainContent.innerHTML = `
      <div class="view-container">
        <div class="view-header"><h1 class="view-title">Your Library</h1></div>
        <div class="grid-container" id="lib-grid">
          <div class="card" onclick="renderView('liked')">
            <div class="card-art-wrap" style="background: linear-gradient(135deg, #450af5, #c4efd9); color: white;">♥</div>
            <div class="card-title">Liked Songs</div>
            <div class="card-desc">${state.likedSongs.length} lagu</div>
          </div>
        </div>
      </div>
    `;
    const grid = document.getElementById('lib-grid');
    state.playlists.forEach(pl => {
      const card = document.createElement('div');
      card.className = 'card';
      card.onclick = () => renderView('playlist', pl.id);
      card.innerHTML = `
        <div class="card-art-wrap" style="background:#282828">${pl.emoji}</div>
        <div class="card-title">${pl.name}</div>
        <div class="card-desc">${pl.desc || pl.songs.length+' lagu'}</div>
      `;
      grid.appendChild(card);
    });
  }
  else if(view === 'liked') {
    mainContent.innerHTML = `
      <div class="pl-header">
        <div class="pl-cover" style="background: linear-gradient(135deg, #450af5, #c4efd9); color: white;">♥</div>
        <div class="pl-info">
          <span>Playlist</span>
          <h1 class="pl-title">Liked Songs</h1>
          <div class="pl-meta">${state.user.name} • ${state.likedSongs.length} lagu</div>
        </div>
      </div>
      <div class="pl-action-bar">
        <button class="btn-play-lg" onclick="state.playTrack(state.likedSongs[0], state.likedSongs)"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></button>
      </div>
      <div class="view-container" style="padding-top:0;">
        <div class="track-list" id="liked-list"></div>
      </div>
    `;
    renderTrackList('liked-list', state.likedSongs, state.likedSongs);
  }
  else if(view === 'playlist') {
    const pl = state.playlists.find(p => p.id === param);
    if(!pl) return renderView('library');
    mainContent.innerHTML = `
      <div class="pl-header">
        <div class="pl-cover" style="background:#282828">${pl.emoji}</div>
        <div class="pl-info">
          <span>Playlist</span>
          <h1 class="pl-title">${pl.name}</h1>
          <div class="pl-desc">${pl.desc}</div>
          <div class="pl-meta">${state.user.name} • ${pl.songs.length} lagu</div>
        </div>
      </div>
      <div class="pl-action-bar">
        <button class="btn-play-lg" onclick="state.playTrack(state.playlists.find(p=>p.id==='${pl.id}').songs[0], state.playlists.find(p=>p.id==='${pl.id}').songs)"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></button>
      </div>
      <div class="view-container" style="padding-top:0;">
        <div class="track-list" id="pl-list"></div>
      </div>
    `;
    renderTrackList('pl-list', pl.songs, pl.songs);
  }
}

function renderGrid(containerId, items, queue) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  items.forEach(t => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-art-wrap">
        ${t.artworkUrl100 ? `<img src="${t.artworkUrl100}" alt=""/>` : '♪'}
        <button class="card-play-btn"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></button>
      </div>
      <div class="card-title">${t.trackName}</div>
      <div class="card-desc">${t.artistName}</div>
    `;
    card.querySelector('.card-play-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      state.playTrack(t, queue);
    });
    container.appendChild(card);
  });
}

function renderTrackList(containerId, items, queue) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  items.forEach((t, i) => {
    const row = document.createElement('div');
    row.className = 'track-row';
    const isPlaying = state.currentTrack && state.currentTrack.trackId === t.trackId;
    if(isPlaying) row.classList.add('active');
    
    // Add to playlist btn
    const addBtn = document.createElement('button');
    addBtn.className = 'icon-btn';
    addBtn.textContent = '+';
    addBtn.title = "Tambah ke Playlist";
    addBtn.onclick = (e) => {
      e.stopPropagation();
      openAddToPlaylist(t);
    };

    row.innerHTML = `
      <div style="position:relative; width:16px;">
        <span class="track-idx">${i+1}</span>
        <svg class="play-btn-sm" viewBox="0 0 24 24" style="position:absolute; top:0; left:0; width:16px; height:16px; fill:currentColor"><path d="M8 5v14l11-7z"/></svg>
      </div>
      <div class="track-info">
        <div class="track-art">${t.artworkUrl100 ? `<img src="${t.artworkUrl100}" alt=""/>` : '♪'}</div>
        <div>
          <div class="track-name">${t.trackName}</div>
          <div class="track-artist">${t.artistName}</div>
        </div>
      </div>
      <div class="track-album">${t.albumName || ''}</div>
      <div class="track-actions">
        <!-- addBtn will be appended here -->
      </div>
    `;
    row.querySelector('.track-actions').appendChild(addBtn);
    
    // Play on click
    row.addEventListener('click', (e) => {
      if(e.target === addBtn) return;
      state.playTrack(t, queue);
    });
    
    container.appendChild(row);
  });
}

// Sidebar Playlists
state.on('playlists_changed', (pls) => {
  const c = document.getElementById('sidebar-playlists');
  c.innerHTML = '';
  pls.forEach(pl => {
    const el = document.createElement('div');
    el.className = 'pl-item';
    el.innerHTML = `<div class="pl-item-art">${pl.emoji}</div><span>${pl.name}</span>`;
    el.onclick = () => {
      document.querySelectorAll('.snav-item').forEach(n => n.classList.remove('active'));
      currentView = 'playlist';
      renderView('playlist', pl.id);
    };
    c.appendChild(el);
  });
});

state.on('liked_changed', () => {
  if(state.currentTrack) {
    const isLiked = state.likedSongs.some(s => s.trackId === state.currentTrack.trackId);
    document.getElementById('pb-like').style.color = isLiked ? 'var(--brand)' : 'var(--text-secondary)';
  }
  if(currentView === 'library' || currentView === 'liked') renderView(currentView);
});

// Modals
document.getElementById('btn-auth-go').addEventListener('click', () => {
  const name = document.getElementById('auth-name').value.trim();
  if(!name) return;
  state.setUser(name);
  document.getElementById('m-auth').classList.add('hidden');
  showApp();
});
document.getElementById('btn-login').addEventListener('click', () => {
  document.getElementById('m-auth').classList.remove('hidden');
});
document.getElementById('btn-signup').addEventListener('click', () => {
  document.getElementById('m-auth').classList.remove('hidden');
});
document.getElementById('btn-start').addEventListener('click', () => {
  document.getElementById('m-auth').classList.remove('hidden');
});
document.getElementById('btn-explore').addEventListener('click', () => {
  document.getElementById('m-auth').classList.remove('hidden');
});

// Playlist Modal
let selectedEmoji = '🎵';
document.querySelectorAll('.ep').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('.ep').forEach(e => e.classList.remove('selected'));
    el.classList.add('selected');
    selectedEmoji = el.dataset.e;
  });
});
document.getElementById('btn-create-pl').addEventListener('click', () => {
  document.getElementById('m-playlist').classList.remove('hidden');
});
document.getElementById('m-pl-close').addEventListener('click', () => {
  document.getElementById('m-playlist').classList.add('hidden');
});
document.getElementById('btn-pl-save').addEventListener('click', async () => {
  const name = document.getElementById('pl-name').value.trim();
  const desc = document.getElementById('pl-desc').value.trim();
  if(!name) return;
  const pl = await api.createPlaylist({name, desc, emoji: selectedEmoji});
  if(pl) {
    const pls = await api.getPlaylists();
    state.setPlaylists(pls);
    document.getElementById('m-playlist').classList.add('hidden');
    document.getElementById('pl-name').value = '';
    document.getElementById('pl-desc').value = '';
  }
});

// Add to Playlist Modal
function openAddToPlaylist(song) {
  document.getElementById('atp-song-data').value = JSON.stringify(song);
  const list = document.getElementById('atp-list');
  list.innerHTML = '';
  state.playlists.forEach(pl => {
    const item = document.createElement('div');
    item.className = 'atp-item';
    item.innerHTML = `<div class="atp-item-art">${pl.emoji}</div><span>${pl.name}</span>`;
    item.onclick = async () => {
      await api.addSongToPlaylist(pl.id, song);
      document.getElementById('m-atp').classList.add('hidden');
      const pls = await api.getPlaylists();
      state.setPlaylists(pls);
    };
    list.appendChild(item);
  });
  document.getElementById('m-atp').classList.remove('hidden');
}
document.getElementById('m-atp-close').addEventListener('click', () => {
  document.getElementById('m-atp').classList.add('hidden');
});

init();
