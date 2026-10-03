/** Abstract audio player interface (`SKILL5` + `local-audio` skill). */

export type PlayerEventType = "play" | "pause" | "ended" | "timeupdate" | "error" | "loadedmetadata";

export interface PlayerEvent {
  readonly type: PlayerEventType;
  readonly payload?: unknown;
}

export type PlayerEventListener = (event: PlayerEvent) => void;

export interface AudioPlayer {
  readonly source: string; // track id
  readonly isPlaying: boolean;
  readonly currentTime: number;
  readonly duration: number;
  readonly volume: number;
  readonly muted: boolean;

  load(source: string, options?: { startTime?: number }): Promise<void>;
  play(): Promise<void>;
  pause(): void;
  seek(time: number): Promise<void>;
  setVolume(volume: number): void;
  setMuted(muted: boolean): void;
  /** Optional: prepare the next track's bytes without playing them (`F12`). */
  preload?(source: string): void;
  destroy(): void;

  on(event: PlayerEventType, listener: PlayerEventListener): () => void;
}