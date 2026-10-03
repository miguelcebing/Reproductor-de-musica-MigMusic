/** YouTube IFrame implementation of `AudioPlayer` (`F8`).

 * Audio plays through YouTube's official embedded player using the track's
 * `videoId`; nothing is downloaded or extracted server-side. The player mounts
 * into a hidden, off-screen host element so the existing custom controls drive
 * it via the shared `AudioPlayer` contract.

 * State handling: `load()` destroys any previous inner player before creating a
 * new one, so switching songs never leaves a stale player echoing audio (the
 * "plays 2 s then jumps back" symptom).
 */

import type { AudioPlayer, PlayerEventType, PlayerEventListener } from "./AudioPlayer";
import {
  loadYouTubeApi,
  type YouTubePlayerInstance,
  type YouTubePlayerVars,
} from "./youtubeIframe";

const HOST_ID = "migmusic-youtube-host";
const POLL_INTERVAL_MS = 500;

export class YouTubePlayer implements AudioPlayer {
  private readonly listeners = new Map<PlayerEventType, Set<PlayerEventListener>>();
  private container: HTMLDivElement | null = null;
  private player: YouTubePlayerInstance | null = null;
  private ticker: ReturnType<typeof setInterval> | null = null;
  private _source = "";
  private _duration = 0;
  private _playing = false;
  private _volume = 1;
  private _muted = false;
  private destroyed = false;
  private endedEmitted = false;

  get source(): string {
    return this._source;
  }

  get isPlaying(): boolean {
    return this._playing;
  }

  get currentTime(): number {
    return this.player?.getCurrentTime() ?? 0;
  }

  get duration(): number {
    return this._duration;
  }

  get volume(): number {
    return this._volume;
  }

  get muted(): boolean {
    return this._muted;
  }

  async load(source: string, options?: { startTime?: number }): Promise<void> {
    this.destroyed = false;
    this.endedEmitted = false;
    this._source = source;
    this.teardownPlayer();

    const api = await loadYouTubeApi();
    if (this.destroyed) return;

    const container = this.ensureContainer();
    const mount = document.createElement("div");
    container.appendChild(mount);

    const playerVars: YouTubePlayerVars = {
      autoplay: 0,
      controls: 0,
      disablekb: 1,
      modestbranding: 1,
      playsinline: 1,
      rel: 0,
      origin: window.location.origin,
    };
    const startTime = Math.max(0, options?.startTime ?? 0);

    this.player = await new Promise<YouTubePlayerInstance>((resolve) => {
      const player = new api.Player(mount, {
        videoId: source,
        playerVars,
        events: {
          onReady: (event) => {
            event.target.setVolume(this._muted ? 0 : this._volume * 100);
            this._duration = event.target.getDuration() || 0;
            if (startTime > 0) event.target.seekTo(startTime, true);
            resolve(player);
          },
          onStateChange: (event) => this.onStateChange(event.data ?? -1, api),
          onError: (event) => this.emit("error", { error: `youtube_error_${event.data}` }),
        },
      });
    });

    this.startTicker();
  }

  async play(): Promise<void> {
    this.player?.playVideo();
    this._playing = true;
  }

  pause(): void {
    this.player?.pauseVideo();
    this._playing = false;
  }

  async seek(time: number): Promise<void> {
    this.player?.seekTo(Math.max(0, time), true);
  }

  setVolume(volume: number): void {
    this._volume = Math.min(1, Math.max(0, volume));
    if (this.player) this.player.setVolume(this._muted ? 0 : this._volume * 100);
  }

  setMuted(muted: boolean): void {
    this._muted = muted;
    if (!this.player) return;
    if (muted) this.player.mute();
    else {
      this.player.unMute();
      this.player.setVolume(this._volume * 100);
    }
  }

  destroy(): void {
    this.destroyed = true;
    this.stopTicker();
    this.teardownPlayer();
    this.container?.remove();
    this.container = null;
    this.listeners.clear();
  }

  on(event: PlayerEventType, listener: PlayerEventListener): () => void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  // ------------------------------------------------------------- internals

  private onStateChange(state: number, api: { PlayerState: { ENDED: number; PLAYING: number; PAUSED: number } }): void {
    if (state === api.PlayerState.PLAYING) {
      this._playing = true;
      this.emit("play");
    } else if (state === api.PlayerState.PAUSED) {
      this._playing = false;
      this.emit("pause");
    } else if (state === api.PlayerState.ENDED) {
      this._playing = false;
      this.emitEnded();
    }
  }

  private startTicker(): void {
    this.stopTicker();
    this.ticker = setInterval(() => {
      if (this.destroyed || !this.player) return;
      this._duration = this.player.getDuration() || this._duration;
      this.emit("timeupdate", { currentTime: this.player.getCurrentTime() });
    }, POLL_INTERVAL_MS);
  }

  private stopTicker(): void {
    if (this.ticker !== null) {
      clearInterval(this.ticker);
      this.ticker = null;
    }
  }

  /** Detach the inner player so a source switch cannot leave it playing. */
  private teardownPlayer(): void {
    this.stopTicker();
    if (this.player) {
      try {
        this.player.stopVideo();
      } catch {
        // The frame may already be gone; destroying below is what matters.
      }
      try {
        this.player.destroy();
      } catch {
        // Ignore: the iframe was removed already.
      }
      this.player = null;
    }
    if (this.container) this.container.innerHTML = "";
    this._playing = false;
    this._duration = 0;
  }

  private ensureContainer(): HTMLDivElement {
    if (this.container) return this.container;
    const existing = document.getElementById(HOST_ID) as HTMLDivElement | null;
    const container = existing ?? document.createElement("div");
    container.id = HOST_ID;
    // Hidden but alive: YouTube refuses to play a display:none iframe reliably,
    // so keep it off-screen instead of `display: none`.
    container.style.position = "fixed";
    container.style.left = "-10000px";
    container.style.top = "0";
    container.style.width = "320px";
    container.style.height = "180px";
    container.style.pointerEvents = "none";
    if (!existing) document.body.appendChild(container);
    this.container = container;
    return container;
  }

  private emitEnded(): void {
    if (this.endedEmitted) return;
    this.endedEmitted = true;
    this.emit("ended");
  }

  private emit(type: PlayerEventType, payload?: unknown): void {
    this.listeners.get(type)?.forEach((listener) => listener({ type, payload }));
  }
}
