/** Transport use cases.

 * The backend owns the position and the modes (`PLAYER-011`): the controller
 * asks for a change and stores the state the server answers with. The audio
 * element itself is introduced in F5 and will report its own position here.
 */

import { ApiClient, ApiError } from "./apiClient";
import type { PlaybackState, RepeatMode, SkipDirection } from "../domain/types";
import { usePlaybackStore } from "../state/playbackStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface PlaybackControllerOptions {
  readonly language: () => Language;
}

export class PlaybackController {
  private readonly api: ApiClient;
  private readonly language: () => Language;

  constructor(api: ApiClient, options: PlaybackControllerOptions) {
    this.api = api;
    this.language = options.language;
  }

  /** Load the transport; a 404 simply means nothing is open yet. */
  async refresh(): Promise<PlaybackState | null> {
    try {
      const state = await this.api.getPlayback();
      usePlaybackStore.getState().setPlayback(state);
      return state;
    } catch (cause) {
      if (cause instanceof ApiError && (cause.status === 404 || cause.code === "not_found")) {
        usePlaybackStore.getState().setPlayback(null);
        return null;
      }
      this.fail(cause);
      return null;
    }
  }

  select(playlistId: string, index: number): Promise<PlaybackState | null> {
    return this.send(() => this.api.selectSong(playlistId, index));
  }

  open(playlistId: string): Promise<PlaybackState | null> {
    return this.send(() => this.api.openPlaylist(playlistId));
  }

  next(): Promise<PlaybackState | null> {
    return this.send(() => this.api.next());
  }

  previous(): Promise<PlaybackState | null> {
    return this.send(() => this.api.previous());
  }

  /** The audio element ended the track (`PLAYER-003 = A`). */
  songFinished(): Promise<PlaybackState | null> {
    return this.send(() => this.api.songFinished());
  }

  skip(direction: SkipDirection): Promise<PlaybackState | null> {
    return this.send(() => this.api.skip(direction));
  }

  seek(position: number): Promise<PlaybackState | null> {
    return this.send(() => this.api.seek(position));
  }

  /** Play/pause until F5 introduces the real audio element. */
  togglePlaying(): Promise<PlaybackState | null> {
    const current = usePlaybackStore.getState().playback;
    if (!current) return Promise.resolve(null);
    return this.send(() => this.api.report(undefined, !current.playing));
  }

  setRepeat(repeat: RepeatMode): Promise<PlaybackState | null> {
    return this.send(() => this.api.setModes({ repeat }));
  }

  toggleShuffle(): Promise<PlaybackState | null> {
    const current = usePlaybackStore.getState().playback;
    if (!current) return Promise.resolve(null);
    return this.send(() => this.api.setModes({ shuffle: !current.shuffle }));
  }

  private async send(request: () => Promise<PlaybackState>): Promise<PlaybackState | null> {
    try {
      const state = await request();
      usePlaybackStore.getState().setPlayback(state);
      return state;
    } catch (cause) {
      this.fail(cause);
      return null;
    }
  }

  private fail(cause: unknown): void {
    const message = cause instanceof Error ? cause.message : String(cause);
    useToastStore
      .getState()
      .push("error", translate(this.language(), "toast.error", { message }));
  }

  /** Exposed for tests that assert the error path without importing stores. */
  static get errorKey(): MessageKey {
    return "toast.error";
  }
}
