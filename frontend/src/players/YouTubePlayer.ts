/** YouTube IFrame implementation of `AudioPlayer` (`F8`, reused in `F12`).
 *
 * Audio plays through YouTube's official embedded player using the track's
 * `videoId`; nothing is downloaded or extracted server-side. The player mounts
 * into a hidden, off-screen host element so the existing custom controls drive
 * it via the shared `AudioPlayer` contract.
 *
 * One iframe is created for the whole session and reused for every track
 * (`F12`): switching songs calls `loadVideoById` on the same instance instead
 * of rebuilding the iframe, which removes the hundreds of milliseconds of
 * player setup on each click. A wrapper is still created per track (it is a
 * thin object), but it only owns listeners and the ticker; the shared engine
 * survives `destroy()` so the next track starts instantly.
 */

import type { AudioPlayer, PlayerEventType, PlayerEventListener } from "./AudioPlayer";
import {
  loadYouTubeApi,
  type YouTubeApi,
  type YouTubePlayerInstance,
  type YouTubePlayerVars,
} from "./youtubeIframe";

const HOST_ID = "migmusic-youtube-host";
const POLL_INTERVAL_MS = 500;

/** The one iframe shared by every wrapper; `owner` is the active wrapper. */
interface YouTubeEngine {
  readonly api: YouTubeApi;
  readonly container: HTMLDivElement;
  readonly mount: HTMLDivElement;
  readonly player: YouTubePlayerInstance;
  videoId: string;
  owner: YouTubePlayer | null;
}

let engine: YouTubeEngine | null = null;
let engineCreation: Promise<YouTubeEngine> | null = null;

/** Create the shared iframe once; the promise is shared by concurrent loads. */
function createEngine(api: YouTubeApi, source: string): Promise<YouTubeEngine> {
  const container = document.createElement("div");
  container.id = HOST_ID;
  // Hidden but alive: YouTube refuses to play a display:none iframe reliably,
  // so keep it off-screen instead of `display: none`.
  Object.assign(container.style, {
    position: "fixed",
    left: "-10000px",
    top: "0",
    width: "320px",
    height: "180px",
    pointerEvents: "none",
  });
  document.body.appendChild(container);

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

  return new Promise<YouTubeEngine>((resolve) => {
    new api.Player(mount, {
      videoId: source,
      playerVars,
      events: {
        onReady: (event) =>
          resolve({ api, container, mount, player: event.target, videoId: source, owner: null }),
        onStateChange: (event) => engine?.owner?.handleStateChange(event.data ?? -1, api),
        onError: (event) => engine?.owner?.handleError(event.data ?? -1),
      },
    });
  });
}

/** Tear down the shared iframe; used on app teardown and in tests. */
export function disposeYouTubeEngine(): void {
  if (!engine) return;
  try {
    engine.player.destroy();
  } catch {
    // The frame may already be gone.
  }
  engine.container.remove();
  engine = null;
}

export class YouTubePlayer implements AudioPlayer {
  private readonly listeners = new Map<PlayerEventType, Set<PlayerEventListener>>();
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
    this._duration = 0;
    this._playing = false;

    const api = await loadYouTubeApi();
    if (this.destroyed) return;

    const shared = await this.ensureEngine(api, source);
    if (this.destroyed) return;

    shared.owner = this;
    this.player = shared.player;
    this.applyVolume();

    const startTime = Math.max(0, options?.startTime ?? 0);
    if (shared.videoId !== source) {
      // Same iframe, new video: no teardown, no player construction.
      shared.videoId = source;
      shared.player.loadVideoById(source, startTime > 0 ? startTime : undefined);
    } else if (startTime > 0) {
      shared.player.seekTo(startTime, true);
    }

    this._duration = shared.player.getDuration() || 0;
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
    this.applyVolume();
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

  /**
   * Detach this wrapper from the shared iframe (`F12`).
   *
   * The iframe itself is kept alive for the next track; only the audio is
   * paused and the owner cleared, so a source switch cannot leave stale audio
   * behind while still avoiding the cost of rebuilding the player.
   */
  destroy(): void {
    this.destroyed = true;
    this.stopTicker();
    if (engine?.owner === this) {
      engine.owner = null;
      try {
        engine.player.pauseVideo();
      } catch {
        // The frame may already be gone.
      }
    }
    this.player = null;
    this.listeners.clear();
  }

  on(event: PlayerEventType, listener: PlayerEventListener): () => void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  // ------------------------------------------------------------- internals

  /** Reuse the live iframe, or create it once (concurrent loads share it). */
  private async ensureEngine(api: YouTubeApi, source: string): Promise<YouTubeEngine> {
    if (engine && document.body.contains(engine.container)) return engine;
    if (!engineCreation) {
      engineCreation = createEngine(api, source)
        .then((created) => {
          engine = created;
          return created;
        })
        .finally(() => {
          engineCreation = null;
        });
    }
    return engineCreation;
  }

  private applyVolume(): void {
    if (this.player) this.player.setVolume(this._muted ? 0 : this._volume * 100);
  }

  /**
   * YouTube error codes that mean "cannot be played embedded" (`100`, `101`,
   * `150`: video missing/private, embedding disabled by the owner, or the
   * owner restricted it). These are not fixable client-side, so the caller
   * shows a friendly message and skips instead of a raw error.
   */
  handleError(code: number): void {
    if (code === 100 || code === 101 || code === 150) {
      this.emit("error", { error: "youtube_unplayable", code });
      return;
    }
    this.emit("error", { error: `youtube_error_${code}`, code });
  }

  handleStateChange(state: number, api: YouTubeApi): void {
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
      if (this.destroyed || !this.player || engine?.owner !== this) return;
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

  private emitEnded(): void {
    if (this.endedEmitted) return;
    this.endedEmitted = true;
    this.emit("ended");
  }

  private emit(type: PlayerEventType, payload?: unknown): void {
    this.listeners.get(type)?.forEach((listener) => listener({ type, payload }));
  }
}
