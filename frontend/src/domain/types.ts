/** Wire contract shared with the backend (see `docs/api.md`). */

/** Where a track comes from; players are polymorphic over this value. */
export type AudioSource = "local" | "spotify";

/** Repeat modes exposed by `POST /api/playback/modes`. */
export type RepeatMode = "off" | "one" | "all";

/** Direction of `POST /api/playback/skip` (the server owns the step size). */
export type SkipDirection = "forward" | "backward";

/** A track as returned by the API, including the computed `m:ss` label. */
export interface Song {
  readonly id: string;
  readonly title: string;
  readonly artist: string;
  readonly source: AudioSource;
  readonly duration: number;
  readonly duration_label: string;
  readonly album: string | null;
  readonly artwork_url: string | null;
  readonly external_url: string | null;
  readonly available: boolean;
}

/** Payload accepted by `POST /api/playlists/{id}/songs`. */
export interface SongInput {
  readonly id: string;
  readonly title: string;
  readonly artist: string;
  readonly source: AudioSource;
  readonly duration?: number;
  readonly album?: string | null;
  readonly artwork_url?: string | null;
  readonly external_url?: string | null;
  readonly available?: boolean;
}

/** A playlist with its songs in list order. */
export interface Playlist {
  readonly id: string;
  readonly name: string;
  readonly size: number;
  readonly current_index: number | null;
  readonly songs: readonly Song[];
}

/** Transport state of the one active playlist. */
export interface PlaybackState {
  readonly playlist_id: string | null;
  readonly song: Song | null;
  readonly index: number | null;
  readonly position: number;
  readonly playing: boolean;
  readonly repeat: RepeatMode;
  readonly shuffle: boolean;
  readonly size: number;
  readonly available_next: boolean;
  readonly available_previous: boolean;
  readonly skip_seconds: number;
}

/** Uniform error body produced by the backend. */
export interface ErrorEnvelope {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

/** Where newly added tracks are inserted (`UX-003`). */
export type TrackPosition = { kind: "start" } | { kind: "end" } | { kind: "index"; index: number };

// --- Spotify (`F6`) ---------------------------------------------------------

/** `GET /api/auth/spotify/status` — whether this session holds Spotify tokens. */
export interface AuthStatus {
  readonly authenticated: boolean;
}

/** `GET /api/auth/spotify/token` — short-lived token for the Web Playback SDK. */
export interface AccessToken {
  readonly access_token: string;
  readonly expires_in: number;
  readonly token_type: "Bearer";
}

/** `POST /api/auth/spotify/callback` — result of the code exchange. */
export interface CallbackResult {
  readonly authenticated: boolean;
}

/** Header of a Spotify playlist (`GET /api/spotify/playlists`). */
export interface SpotifyPlaylist {
  readonly id: string;
  readonly name: string;
  readonly track_count: number;
  readonly artwork_url: string | null;
}

/** `GET /api/spotify/player/state` — simplified SDK-synced playback state. */
export interface SpotifyPlayerState {
  readonly playing: boolean;
  readonly position_ms: number;
  readonly duration_ms: number;
  readonly track_uri: string | null;
  readonly volume_percent: number | null;
  readonly device_id: string | null;
}
