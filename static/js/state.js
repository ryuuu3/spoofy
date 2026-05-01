class AppState {
  constructor() {
    this.user = { name: localStorage.getItem('spoofy_user') || null };
    this.playlists = [];
    this.likedSongs = [];
    this.queue = [];
    this.currentTrack = null;
    this.currentIndex = -1;
    this.isPlaying = false;
    this.listeners = {};
  }

  on(event, cb) {
    if(!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(cb);
  }

  emit(event, data) {
    if(this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }

  setUser(name) {
    this.user.name = name;
    localStorage.setItem('spoofy_user', name);
    this.emit('user_changed', this.user);
  }

  setPlaylists(lists) {
    this.playlists = lists;
    this.emit('playlists_changed', this.playlists);
  }

  setLiked(songs) {
    this.likedSongs = songs;
    this.emit('liked_changed', this.likedSongs);
  }

  playTrack(track, queue = null) {
    if(queue) {
      this.queue = queue;
      this.currentIndex = this.queue.findIndex(t => t.trackId === track.trackId);
    }
    this.currentTrack = track;
    this.isPlaying = true;
    this.emit('track_changed', track);
  }

  togglePlay() {
    if(!this.currentTrack) return;
    this.isPlaying = !this.isPlaying;
    this.emit('play_toggled', this.isPlaying);
  }

  nextTrack() {
    if(this.queue.length === 0) return;
    this.currentIndex = (this.currentIndex + 1) % this.queue.length;
    this.playTrack(this.queue[this.currentIndex]);
  }

  prevTrack() {
    if(this.queue.length === 0) return;
    this.currentIndex = (this.currentIndex - 1 + this.queue.length) % this.queue.length;
    this.playTrack(this.queue[this.currentIndex]);
  }
}

const state = new AppState();
