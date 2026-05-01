const api = {
  async fetch(url, options = {}) {
    try {
      const res = await fetch(url, options);
      if(!res.ok) throw new Error('API Error');
      return await res.json();
    } catch(err) {
      console.error(err);
      return null;
    }
  },

  async search(query) {
    return this.fetch(`/api/search?q=${encodeURIComponent(query)}`);
  },

  async trending() {
    return this.fetch(`/api/trending`);
  },

  async getStreamUrl(trackId) {
    const data = await this.fetch(`/api/stream/${trackId}`);
    return data ? data.url : null;
  },

  async getLyrics(artist, track) {
    return this.fetch(`/api/lyrics?artist=${encodeURIComponent(artist)}&track=${encodeURIComponent(track)}`);
  },

  async getPlaylists() {
    return this.fetch('/api/playlists') || [];
  },

  async createPlaylist(data) {
    return this.fetch('/api/playlists', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {'Content-Type': 'application/json'}
    });
  },

  async getLiked() {
    return this.fetch('/api/liked') || [];
  },

  async toggleLike(song, isLiked) {
    if(isLiked) {
      return this.fetch(`/api/liked/${song.trackId}`, { method: 'DELETE' });
    } else {
      return this.fetch('/api/liked', {
        method: 'POST',
        body: JSON.stringify(song),
        headers: {'Content-Type': 'application/json'}
      });
    }
  },

  async addSongToPlaylist(pid, song) {
    return this.fetch(`/api/playlists/${pid}/songs`, {
      method: 'POST',
      body: JSON.stringify(song),
      headers: {'Content-Type': 'application/json'}
    });
  }
};
