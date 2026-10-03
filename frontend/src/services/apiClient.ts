/** Typed HTTP client for the MigMusic API.

 * URL helpers stay pure (unit tested); the class owns everything that talks
 * to the network so controllers never touch `fetch` directly.
 */

import type {
  AccessToken,
  AuthStatus,
  CallbackResult,
  ErrorEnvelope,
  PlaybackState,
  Playlist,
  RepeatMode,
  SkipDirection,
  Song,
  SongFound,
  SongInput,
  SpotifyPlaylist,
  SpotifyPlayerState,
} from "../domain/types";
import { translate, type Language } from "../i18n/messages";
import { getDeviceId } from "./deviceId";

/** Nothing in this API legitimately takes longer; a hung button is worse. */
export const REQUEST_TIMEOUT_MS = 10_000;

/** Development uses the Vite proxy; production goes through Vercel's /api rewrite. */
export function resolveApiBaseUrl(origin: string): string {
  if (typeof origin !== "string" || origin.length === 0) {
    throw new TypeError("origin must be a non-empty string");
  }
  return `${origin.replace(/\/+$/, "")}/api`;
}

/** Build the URL for an API route, keeping exactly one slash between segments. */
export function apiUrl(base: string, path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base.replace(/\/+$/, "")}${normalizedPath}`;
}

/** A non-2xx response, carrying the machine-readable code from the envelope. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | undefined;

  constructor(status: number, code: string, message: string, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

/** Anything shaped like `fetch`, so tests never touch the network. */
export type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

/** Human-readable text for a failure; the timeout gets a localised copy. */
export function failureMessage(cause: unknown, language: Language): string {
  if (cause instanceof ApiError && cause.code === "timeout") {
    return translate(language, "toast.timeout");
  }
  return cause instanceof Error ? cause.message : String(cause);
}

const defaultFetch: FetchLike = (url, init) => fetch(url, init);

export class ApiClient {
  private readonly base: string;
  private readonly request: FetchLike;

  constructor(base: string, fetchImpl: FetchLike = defaultFetch) {
    this.base = base.replace(/\/+$/, "");
    this.request = fetchImpl;
  }

  /** Static entry point: the browser origin in dev and prod alike. */
  static fromOrigin(origin: string, fetchImpl?: FetchLike): ApiClient {
    return new ApiClient(resolveApiBaseUrl(origin), fetchImpl);
  }

  // --- Playlists -----------------------------------------------------------

  listPlaylists(): Promise<Playlist[]> {
    return this.send<Playlist[]>("GET", "/playlists");
  }

  createPlaylist(name: string): Promise<Playlist> {
    return this.send<Playlist>("POST", "/playlists", { name });
  }

  getPlaylist(id: string): Promise<Playlist> {
    return this.send<Playlist>("GET", `/playlists/${encodeURIComponent(id)}`);
  }

  renamePlaylist(id: string, name: string): Promise<Playlist> {
    return this.send<Playlist>("PATCH", `/playlists/${encodeURIComponent(id)}`, { name });
  }

  deletePlaylist(id: string): Promise<void> {
    return this.send<void>("DELETE", `/playlists/${encodeURIComponent(id)}`);
  }

  addSong(playlistId: string, song: SongInput, index?: number): Promise<Playlist> {
    const body = index === undefined ? { song } : { song, index };
    return this.send<Playlist>("POST", `/playlists/${encodeURIComponent(playlistId)}/songs`, body);
  }

  removeSong(playlistId: string, index: number): Promise<Song> {
    return this.send<Song>(
      "DELETE",
      `/playlists/${encodeURIComponent(playlistId)}/songs/${index}`,
    );
  }

  moveSong(playlistId: string, fromIndex: number, toIndex: number): Promise<Playlist> {
    return this.send<Playlist>("PUT", `/playlists/${encodeURIComponent(playlistId)}/songs/order`, {
      from_index: fromIndex,
      to_index: toIndex,
    });
  }

  selectSong(playlistId: string, index: number): Promise<PlaybackState> {
    return this.send<PlaybackState>(
      "POST",
      `/playlists/${encodeURIComponent(playlistId)}/songs/${index}/select`,
    );
  }

  /** First song matching `text` (case-insensitive title/artist); `404` on a miss. */
  findSong(playlistId: string, text: string): Promise<SongFound> {
    const params = new URLSearchParams({ text });
    return this.send<SongFound>(
      "GET",
      `/playlists/${encodeURIComponent(playlistId)}/songs/find?${params.toString()}`,
    );
  }

  /** Idempotent heart (`FEAT-001-b`): returns the updated song. */
  setFavorite(playlistId: string, index: number, favorite: boolean): Promise<Song> {
    return this.send<Song>(
      "PUT",
      `/playlists/${encodeURIComponent(playlistId)}/songs/${index}/favorite`,
      { favorite },
    );
  }

  // --- Playback ------------------------------------------------------------

  getPlayback(): Promise<PlaybackState> {
    return this.send<PlaybackState>("GET", "/playback");
  }

  openPlaylist(playlistId: string): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/open", { playlist_id: playlistId });
  }

  next(): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/next");
  }

  previous(): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/previous");
  }

  songFinished(): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/finished");
  }

  skip(direction: SkipDirection): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/skip", { direction });
  }

  seek(position: number): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/seek", { position });
  }

  report(position?: number, playing?: boolean): Promise<PlaybackState> {
    const body: { position?: number; playing?: boolean } = {};
    if (position !== undefined) body.position = position;
    if (playing !== undefined) body.playing = playing;
    return this.send<PlaybackState>("POST", "/playback/report", body);
  }

  setModes(modes: { repeat?: RepeatMode; shuffle?: boolean }): Promise<PlaybackState> {
    return this.send<PlaybackState>("POST", "/playback/modes", modes);
  }

  health(): Promise<{ status: string; service: string; environment: string }> {
    return this.send<{ status: string; service: string; environment: string }>("GET", "/health");
  }

  // --- Spotify auth (`F6`) --------------------------------------------------

  /** Absolute URL the browser navigates to in order to start the OAuth flow. */
  spotifyLoginUrl(): string {
    return apiUrl(this.base, "/auth/spotify/login");
  }

  spotifyStatus(): Promise<AuthStatus> {
    return this.send<AuthStatus>("GET", "/auth/spotify/status");
  }

  spotifyToken(): Promise<AccessToken> {
    return this.send<AccessToken>("GET", "/auth/spotify/token");
  }

  spotifyCallback(code: string, state: string): Promise<CallbackResult> {
    return this.send<CallbackResult>("POST", "/auth/spotify/callback", { code, state });
  }

  spotifyLogout(): Promise<void> {
    return this.send<void>("POST", "/auth/spotify/logout");
  }

  // --- Spotify catalog (`F6`) -----------------------------------------------

  // Spotify answers 400 "Invalid limit" above 10 results, so the default
  // (and the only safe page size) is 10.
  searchSpotify(query: string, limit = 10): Promise<Song[]> {
    const params = `?q=${encodeURIComponent(query)}&limit=${limit}`;
    return this.send<Song[]>("GET", `/spotify/search${params}`);
  }

  savedSpotify(limit = 20): Promise<Song[]> {
    return this.send<Song[]>("GET", `/spotify/saved?limit=${limit}`);
  }

  listSpotifyPlaylists(limit = 20): Promise<SpotifyPlaylist[]> {
    return this.send<SpotifyPlaylist[]>("GET", `/spotify/playlists?limit=${limit}`);
  }

  spotifyPlaylistTracks(playlistId: string, limit = 50): Promise<Song[]> {
    return this.send<Song[]>(
      "GET",
      `/spotify/playlists/${encodeURIComponent(playlistId)}/tracks?limit=${limit}`,
    );
  }

  // --- YouTube Music catalog (`F8`) -----------------------------------------

  searchYouTube(query: string, limit = 20): Promise<Song[]> {
    const params = `?q=${encodeURIComponent(query)}&limit=${limit}`;
    return this.send<Song[]>("GET", `/youtube/search${params}`);
  }

  // --- Spotify player proxy (`F6`) ------------------------------------------

  spotifyPlay(params: {
    uris?: readonly string[];
    device_id?: string;
    position_ms?: number;
  }): Promise<void> {
    return this.send<void>("PUT", "/spotify/player/play", params);
  }

  spotifyPause(deviceId?: string): Promise<void> {
    return this.send<void>("PUT", "/spotify/player/pause", { device_id: deviceId });
  }

  spotifyNext(deviceId?: string): Promise<void> {
    return this.send<void>("POST", "/spotify/player/next", { device_id: deviceId });
  }

  spotifyPrevious(deviceId?: string): Promise<void> {
    return this.send<void>("POST", "/spotify/player/previous", { device_id: deviceId });
  }

  spotifySeek(positionMs: number, deviceId?: string): Promise<void> {
    return this.send<void>("PUT", "/spotify/player/seek", {
      position_ms: Math.max(0, Math.round(positionMs)),
      device_id: deviceId,
    });
  }

  spotifySetVolume(volumePercent: number, deviceId?: string): Promise<void> {
    const clamped = Math.min(100, Math.max(0, Math.round(volumePercent)));
    return this.send<void>("PUT", "/spotify/player/volume", {
      volume_percent: clamped,
      device_id: deviceId,
    });
  }

  /** Current state; a `404` means nothing is playing on Spotify. */
  spotifyPlayerState(): Promise<SpotifyPlayerState> {
    return this.send<SpotifyPlayerState>("GET", "/spotify/player/state");
  }

  // --- Plumbing ------------------------------------------------------------

  private async send<T>(method: string, path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method, headers: { accept: "application/json" }, credentials: "include" };
    // The backend scopes every playlist/playback call to this id, so it is
    // always sent (an ephemeral id is minted when storage is unavailable).
    (init.headers as Record<string, string>)["x-device-id"] = getDeviceId();
    if (body !== undefined) {
      init.body = JSON.stringify(body);
      (init.headers as Record<string, string>)["content-type"] = "application/json";
    }

    // A sleeping backend (Render free) must surface as a fast, clear toast
    // instead of a button that stays silent until the browser gives up.
    const controller = new AbortController();
    init.signal = controller.signal;
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const response = await this.request(apiUrl(this.base, path), init);
      if (!response.ok) {
        throw await ApiClient.toError(response);
      }
      if (response.status === 204) {
        return undefined as T;
      }
      return (await response.json()) as T;
    } catch (cause) {
      if (controller.signal.aborted) {
        throw new ApiError(0, "timeout", "request timed out");
      }
      if (cause instanceof ApiError) throw cause;
      throw new ApiError(
        0,
        "network_error",
        cause instanceof Error ? cause.message : "network request failed",
      );
    } finally {
      clearTimeout(timer);
    }
  }

  private static async toError(response: Response): Promise<ApiError> {
    let code = "unknown_error";
    let message = response.statusText || `HTTP ${response.status}`;
    let requestId: string | undefined;
    try {
      const payload = (await response.json()) as Partial<ErrorEnvelope>;
      if (payload.error) {
        code = payload.error.code || code;
        message = payload.error.message || message;
        requestId = payload.error.request_id;
      }
    } catch {
      // Non-JSON body: keep the status-derived message.
    }
    return new ApiError(response.status, code, message, requestId);
  }
}
