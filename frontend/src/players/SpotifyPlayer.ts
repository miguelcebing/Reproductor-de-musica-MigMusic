/** Web Playback SDK implementation of `AudioPlayer` (`SKILL3`, `F6`).

 * Playback is started through the backend proxy (`PUT /api/spotify/player/play`
 * with `device_id` + `uris`) and then driven by the SDK session. The session
 * and the transport are injected, so the player is fully unit-testable.
 */

import type { AudioPlayer, PlayerEventType, PlayerEventListener } from "./AudioPlayer";
import type { SpotifySdkSession, SpotifySdkState } from "./spotifySdk";

/** The slice of the player proxy this class needs (keeps tests free of HTTP). */
export interface SpotifyPlaybackControl {
  /** Start (or resume into) `uris` on the SDK device. */
  play(uris: readonly string[], deviceId: string, positionMs?: number): Promise<void>;
}

export interface SpotifyPlayerOptions {
  readonly control: SpotifyPlaybackControl;
  readonly session: SpotifySdkSession;
}

const START_TIMEOUT_MS = 5_000;
const POLL_INTERVAL_MS = 1_000;
const START_POLL_MS = 250;
/** A track is "finished" when it sits paused this close to its duration. */
const END_EPSILON_SECONDS = 0.5;

/** Normalise a raw Spotify id or a URI onto the `spotify:track:` form. */
function toTrackUri(source: string): string {
  return source.startsWith("spotify:") ? source : `spotify:track:${source}`;
}

export class SpotifyPlayer implements AudioPlayer {
  private readonly control: SpotifyPlaybackControl;
  private readonly session: SpotifySdkSession;
  private readonly listeners = new Map<PlayerEventType, Set<PlayerEventListener>>();
  private unsubscribeState: (() => void) | null = null;
  private unsubscribeError: (() => void) | null = null;
  private ticker: ReturnType<typeof setInterval> | null = null;
  private _source = "";
  private state: SpotifySdkState | null = null;
  private stateSeenAt = 0;
  private _volume = 1;
  private _muted = false;
  private destroyed = false;
  private pendingPause: Promise<void> | null = null;
  private endedEmitted = false;

  constructor(options: SpotifyPlayerOptions) {
    this.control = options.control;
    this.session = options.session;
  }

  get source(): string {
    return this._source;
  }

  get isPlaying(): boolean {
    return this.state !== null && !this.state.paused && this.state.uri === this._source;
  }

  get currentTime(): number {
    if (!this.state) return 0;
    const base = this.state.position;
    if (this.state.uri !== this._source || this.state.paused) return base;
    const elapsed = Math.max(0, Date.now() - this.stateSeenAt) / 1000;
    return Math.min(base + elapsed, this.duration);
  }

  get duration(): number {
    if (!this.state || this.state.uri !== this._source) return 0;
    return this.state.duration;
  }

  get volume(): number {
    return this._volume;
  }

  get muted(): boolean {
    return this._muted;
  }

  /** Connect the SDK, queue `source` and wait for it to start playing.

   * `source` may be a raw Spotify track id or a full `spotify:track:…` URI;
   * the SDK always receives the URI form.
   */
  async load(source: string, options?: { startTime?: number }): Promise<void> {
    this.destroyed = false;
    this.endedEmitted = false;
    this._source = toTrackUri(source);
    await this.session.ensureConnected();
    this.subscribe();
    const positionMs = Math.max(0, Math.round((options?.startTime ?? 0) * 1000));
    await this.control.play([this._source], this.session.deviceId, positionMs);
    await this.awaitTrack(this._source);
    this.startTicker();
  }

  async play(): Promise<void> {
    // A pause may still be in flight (fire-and-forget in `pause()`); resume
    // only after it lands so the last command wins.
    if (this.pendingPause) {
      await this.pendingPause;
      this.pendingPause = null;
    }
    await this.session.resume();
  }

  pause(): void {
    this.pendingPause = this.session.pause().catch((cause: unknown) => this.notifyError(cause));
  }

  async seek(time: number): Promise<void> {
    const clamped = Math.min(Math.max(0, time), this.duration || time);
    await this.session.seek(clamped);
    if (this.state) {
      this.applyState({ ...this.state, position: clamped });
    }
  }

  setVolume(volume: number): void {
    this._volume = Math.min(1, Math.max(0, volume));
    void this.session.setVolume(this.effectiveVolume()).catch((cause: unknown) =>
      this.notifyError(cause),
    );
  }

  setMuted(muted: boolean): void {
    this._muted = muted;
    void this.session.setVolume(this.effectiveVolume()).catch((cause: unknown) =>
      this.notifyError(cause),
    );
  }

  /** Stop listening; the shared SDK device stays alive for the next track. */
  destroy(): void {
    this.destroyed = true;
    this.stopTicker();
    this.unsubscribeState?.();
    this.unsubscribeState = null;
    this.unsubscribeError?.();
    this.unsubscribeError = null;
    this.listeners.clear();
    this.state = null;
  }

  on(event: PlayerEventType, listener: PlayerEventListener): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  private effectiveVolume(): number {
    return this._muted ? 0 : this._volume;
  }

  private subscribe(): void {
    this.unsubscribeState?.();
    this.unsubscribeError?.();
    this.unsubscribeState = this.session.onStateChanged((state) => this.applyState(state));
    this.unsubscribeError = this.session.onError((message) =>
      this.emit("error", { message, error: message }),
    );
  }

  /** Poll the SDK so the UI gets a steady stream of `timeupdate` events. */
  private startTicker(): void {
    this.stopTicker();
    this.ticker = setInterval(() => {
      if (this.destroyed) return;
      void this.session
        .getState()
        .then((state) => this.applyState(state))
        .catch((cause: unknown) => this.notifyError(cause));
    }, POLL_INTERVAL_MS);
  }

  private stopTicker(): void {
    if (this.ticker !== null) {
      clearInterval(this.ticker);
      this.ticker = null;
    }
  }

  /** Resolve once the SDK reports `uri` as the current track (bounded wait). */
  private async awaitTrack(uri: string): Promise<void> {
    const deadline = Date.now() + START_TIMEOUT_MS;
    for (;;) {
      const state = await this.session.getState();
      if (state) this.applyState(state);
      if (state?.uri === uri) return;
      if (Date.now() >= deadline) {
        throw new Error("Spotify did not start playing the requested track");
      }
      await new Promise((resolve) => setTimeout(resolve, START_POLL_MS));
    }
  }

  private applyState(state: SpotifySdkState | null): void {
    if (this.destroyed) return;
    const previous = this.state;
    this.state = state;
    this.stateSeenAt = Date.now();

    if (previous && state && previous.uri !== state.uri && previous.uri === this._source) {
      this.emitEnded();
    } else if (previous && !state && previous.uri === this._source) {
      this.emitEnded();
    } else if (state && this.reachedEnd(state)) {
      // The SDK reports a finished track as "paused at the end"; without this
      // branch the queue would never advance (`PLAYER-003`).
      this.emitEnded();
    } else if (previous && state && previous.paused !== state.paused) {
      this.emit(state.paused ? "pause" : "play");
    }

    // Only emit while actually playing: a paused ticker would keep telling the
    // controller `playing: true` and un-pause the UI every second.
    if (state && state.uri === this._source && !state.paused) {
      this.emit("timeupdate", { currentTime: this.currentTime });
    }
  }

  private reachedEnd(state: SpotifySdkState): boolean {
    return (
      state.uri === this._source &&
      state.paused &&
      state.duration > 0 &&
      state.position >= state.duration - END_EPSILON_SECONDS
    );
  }

  /** Fire `ended` at most once per loaded track (polls would repeat it). */
  private emitEnded(): void {
    if (this.endedEmitted) return;
    this.endedEmitted = true;
    this.emit("ended");
  }

  private notifyError(cause: unknown): void {
    this.emit("error", { error: cause });
  }

  private emit(type: PlayerEventType, payload?: unknown): void {
    this.listeners.get(type)?.forEach((listener) => listener({ type, payload }));
  }
}
