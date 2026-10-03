/** Lyrics use cases: fetch a track's lyrics and cache them per song (`F13`).
 *
 * A miss (204) and a failure are both cached as `null`/error so replaying a
 * song never hits the network twice, and neither ever interrupts playback.
 */

import { ApiClient, failureMessage } from "./apiClient";
import type { Lyrics, Song } from "../domain/types";
import { useToastStore } from "../state/toastStore";
import { translate, type Language } from "../i18n/messages";

export type LyricsResult =
  | { readonly status: "ok"; readonly lyrics: Lyrics }
  | { readonly status: "empty" }
  | { readonly status: "error" };

export interface LyricsControllerOptions {
  readonly language: () => Language;
}

/** Cache one settled outcome per track id: nothing is asked twice (`F13`). */
const cache = new Map<string, LyricsResult>();

export class LyricsController {
  private readonly api: ApiClient;
  private readonly language: () => Language;

  constructor(api: ApiClient, options: LyricsControllerOptions) {
    this.api = api;
    this.language = options.language;
  }

  /** Resolve the lyrics for a song, memoised for the session. */
  async forSong(song: Song): Promise<LyricsResult> {
    const cached = cache.get(song.id);
    if (cached) return cached;
    try {
      const lyrics = await this.api.getLyrics({
        id: song.id,
        title: song.title,
        artist: song.artist,
        duration: song.duration,
        source: song.source,
      });
      const result: LyricsResult = lyrics ? { status: "ok", lyrics } : { status: "empty" };
      cache.set(song.id, result);
      return result;
    } catch (cause) {
      const result: LyricsResult = { status: "error" };
      cache.set(song.id, result);
      this.fail(cause);
      return result;
    }
  }

  /** Drop every cached answer (tests). */
  static clearCache(): void {
    cache.clear();
  }

  private fail(cause: unknown): void {
    useToastStore
      .getState()
      .push("error", translate(this.language(), "toast.error", { message: failureMessage(cause, this.language()) }));
  }
}
