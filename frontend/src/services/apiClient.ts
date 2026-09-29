/** Typed HTTP client for the MigMusic API.

 * URL helpers stay pure (unit tested); the class owns everything that talks
 * to the network so controllers never touch `fetch` directly.
 */

import type {
  ErrorEnvelope,
  PlaybackState,
  Playlist,
  RepeatMode,
  SkipDirection,
  Song,
  SongInput,
} from "../domain/types";

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

  // --- Plumbing ------------------------------------------------------------

  private async send<T>(method: string, path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method, headers: { accept: "application/json" } };
    if (body !== undefined) {
      init.body = JSON.stringify(body);
      (init.headers as Record<string, string>)["content-type"] = "application/json";
    }

    let response: Response;
    try {
      response = await this.request(apiUrl(this.base, path), init);
    } catch (cause) {
      throw new ApiError(
        0,
        "network_error",
        cause instanceof Error ? cause.message : "network request failed",
      );
    }

    if (!response.ok) {
      throw await ApiClient.toError(response);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
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
