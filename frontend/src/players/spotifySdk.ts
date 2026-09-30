/** Web Playback SDK loader and typed session (`SKILL3`).

 * The script is loaded lazily from `sdk.scdn.co`; the raw SDK objects are
 * hidden behind {@link SpotifySdkSession} so `SpotifyPlayer` (and its tests)
 * never touch the DOM or the real SDK.
 */

/** Snapshot of the SDK playback state, normalised to seconds. */
export interface SpotifySdkState {
  /** URI of the track being played, or `null` when playback stopped. */
  readonly uri: string | null;
  readonly paused: boolean;
  /** Playhead position in seconds. */
  readonly position: number;
  /** Track duration in seconds. */
  readonly duration: number;
  /** Error message from SDK (account_error, authentication_error, etc.) */
  readonly error?: string | null;
}

/** Everything `SpotifyPlayer` needs from the Web Playback SDK. */
export interface SpotifySdkSession {
  /** Id of the connected SDK device; valid once `ensureConnected` resolves. */
  readonly deviceId: string;
  /** Load the SDK and connect the player once (idempotent). */
  ensureConnected(): Promise<void>;
  /** Tear the player down; safe to call more than once. */
  disconnect(): void;
  resume(): Promise<void>;
  pause(): Promise<void>;
  /** Move the playhead, in seconds. */
  seek(seconds: number): Promise<void>;
  /** Volume in the `[0, 1]` range. */
  setVolume(volume: number): Promise<void>;
  getState(): Promise<SpotifySdkState | null>;
  /** Subscribe to `player_state_changed`; returns the unsubscribe function. */
  onStateChanged(listener: (state: SpotifySdkState | null) => void): () => void;
  /** Subscribe to SDK failures (`account_error`, `authentication_error`, …). */
  onError(listener: (message: string) => void): () => void;
}

// --- Raw SDK shapes (only what we touch) ------------------------------------

interface RawPlayerState {
  readonly paused: boolean;
  readonly position: number;
  readonly duration?: number;
  readonly track_window?: {
    readonly current_track?: { readonly uri: string; readonly duration_ms: number } | null;
  };
}

interface RawPlayer {
  connect(): Promise<boolean>;
  disconnect(): void;
  addListener(event: "ready", cb: (data: { device_id: string }) => void): boolean;
  addListener(event: "player_state_changed", cb: (state: RawPlayerState | null) => void): boolean;
  addListener(
    event:
      | "initialization_error"
      | "authentication_error"
      | "account_error"
      | "playback_error"
      | "not_ready",
    cb: (data: { message?: string }) => void,
  ): boolean;
  removeListener(event: string, cb?: (payload: never) => void): boolean;
  getCurrentState(): Promise<RawPlayerState | null>;
  pause(): Promise<void>;
  resume(): Promise<void>;
  seek(positionMs: number): Promise<void>;
  setVolume(volume: number): Promise<void>;
}

interface RawPlayerOptions {
  name: string;
  getOAuthToken: (cb: (token: string) => void) => void;
  volume?: number;
}

interface SpotifyGlobal {
  Player: new (options: RawPlayerOptions) => RawPlayer;
}

declare global {
  interface Window {
    Spotify?: SpotifyGlobal;
  }
}

const SDK_SCRIPT_URL = "https://sdk.scdn.co/spotify-player.js";
const SDK_TIMEOUT_MS = 10_000;

let sdkLoading: Promise<void> | null = null;

/** Append the official SDK script once and resolve when `Spotify` exists. */
export function loadSpotifySdk(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Spotify Web Playback SDK needs a browser"));
  }
  if (window.Spotify?.Player) return Promise.resolve();
  sdkLoading ??= new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${SDK_SCRIPT_URL}"]`,
    );
    const script = existing ?? document.createElement("script");
    const timer = window.setTimeout(
      () => reject(new Error("Spotify Web Playback SDK timed out")),
      SDK_TIMEOUT_MS,
    );
    const done = (result: Error | null): void => {
      window.clearTimeout(timer);
      if (result) {
        sdkLoading = null;
        reject(result);
        return;
      }
      if (window.Spotify?.Player) {
        resolve();
      } else {
        sdkLoading = null;
        reject(new Error("Spotify Web Playback SDK loaded without a Player"));
      }
    };
    script.addEventListener("load", () => done(null), { once: true });
    script.addEventListener("error", () => done(new Error("Could not load the Spotify SDK")), {
      once: true,
    });
    if (!existing) {
      script.src = SDK_SCRIPT_URL;
      script.async = true;
      document.head.appendChild(script);
    }
  });
  return sdkLoading;
}

function mapState(raw: RawPlayerState | null): SpotifySdkState | null {
  if (!raw) return null;
  const current = raw.track_window?.current_track ?? null;
  return {
    uri: current?.uri ?? null,
    paused: raw.paused,
    position: Math.max(0, raw.position ?? 0) / 1000,
    duration: (current?.duration_ms ?? raw.duration ?? 0) / 1000,
    error: (raw as any).error ?? null,
  };
}

/** Real SDK-backed session; created lazily by `PlayerFactory`. */
export class WebPlaybackSession implements SpotifySdkSession {
  private readonly getToken: () => Promise<string>;
  private readonly stateListeners = new Set<(state: SpotifySdkState | null) => void>();
  private readonly errorListeners = new Set<(message: string) => void>();
  private player: RawPlayer | null = null;
  private _deviceId = "";
  private connecting: Promise<void> | null = null;

  constructor(getToken: () => Promise<string>) {
    this.getToken = getToken;
  }

  get deviceId(): string {
    return this._deviceId;
  }

  async ensureConnected(): Promise<void> {
    if (this.player && this._deviceId) return;
    this.connecting ??= this.connect();
    try {
      await this.connecting;
    } catch (cause) {
      this.connecting = null;
      throw cause;
    }
  }

  disconnect(): void {
    this.player?.disconnect();
    this.player = null;
    this._deviceId = "";
    this.connecting = null;
  }

  async resume(): Promise<void> {
    await this.requirePlayer().resume();
  }

  async pause(): Promise<void> {
    await this.requirePlayer().pause();
  }

  async seek(seconds: number): Promise<void> {
    await this.requirePlayer().seek(Math.max(0, Math.round(seconds * 1000)));
  }

  async setVolume(volume: number): Promise<void> {
    await this.requirePlayer().setVolume(Math.min(1, Math.max(0, volume)));
  }

  async getState(): Promise<SpotifySdkState | null> {
    if (!this.player) return null;
    return mapState(await this.player.getCurrentState());
  }

  onStateChanged(listener: (state: SpotifySdkState | null) => void): () => void {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }

  onError(listener: (message: string) => void): () => void {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  private requirePlayer(): RawPlayer {
    if (!this.player) throw new Error("Spotify player is not connected");
    return this.player;
  }

  private async connect(): Promise<void> {
    await loadSpotifySdk();
    const api = window.Spotify;
    if (!api?.Player) throw new Error("Spotify Web Playback SDK is unavailable");

    // Fail fast with a clear message when the session is not linked yet.
    await this.getToken();

    const player = new api.Player({
      name: "MigMusic",
      getOAuthToken: (cb) => {
        this.getToken().then(
          (token) => cb(token),
          (cause: unknown) => {
            this.notifyError(
              cause instanceof Error ? cause.message : "Spotify session is not available",
            );
            cb("");
          },
        );
      },
    });

    player.addListener("ready", (data) => {
      this._deviceId = data.device_id;
    });
    player.addListener("player_state_changed", (state) => {
      const mapped = mapState(state);
      this.stateListeners.forEach((listener) => listener(mapped));
    });
    for (const event of [
      "initialization_error",
      "authentication_error",
      "account_error",
      "playback_error",
    ] as const) {
      player.addListener(event, (data) => {
        this.notifyError(data.message ?? `Spotify ${event.replace("_", " ")}`);
      });
    }
    player.addListener("not_ready", (data) => {
      this.notifyError(data.message ?? "Spotify device disconnected");
    });

    const connected = await player.connect();
    if (!connected) {
      player.disconnect();
      throw new Error("Spotify player could not connect");
    }
    this.player = player;

    // `ready` usually fires right after connecting; wait briefly for the id.
    for (let attempt = 0; attempt < 40 && !this._deviceId; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (!this._deviceId) {
      throw new Error("Spotify player did not report a device id");
    }
  }

  private notifyError(message: string): void {
    this.errorListeners.forEach((listener) => listener(message));
  }
}
