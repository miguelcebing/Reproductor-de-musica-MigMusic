/** YouTube Music catalog use cases: search results land in the store (`F8`).

 * Keyless and free: the backend proxies the unofficial `ytmusicapi`. Components
 * never call the API directly; they ask the controller and read the store.
 */

import { ApiClient, failureMessage } from "./apiClient";
import type { Song } from "../domain/types";
import { useYouTubeStore } from "../state/youtubeStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface YouTubeControllerOptions {
  readonly language: () => Language;
}

export class YouTubeController {
  private readonly api: ApiClient;
  private readonly language: () => Language;

  constructor(api: ApiClient, options: YouTubeControllerOptions) {
    this.api = api;
    this.language = options.language;
  }

  /** Search YouTube Music and publish the (possibly empty) result list. */
  async search(query: string): Promise<readonly Song[]> {
    const trimmed = query.trim();
    const store = useYouTubeStore.getState();
    store.setQuery(query);
    if (trimmed.length === 0) {
      store.setResults([]);
      return [];
    }
    store.setLoading(true);
    try {
      const results = await this.api.searchYouTube(trimmed);
      useYouTubeStore.getState().setResults(results);
      if (results.length === 0) this.toast("info", "youtube.noResults");
      return results;
    } catch (cause) {
      // A YouTube failure must never break Spotify or local playback.
      this.fail(cause);
      useYouTubeStore.getState().setResults([]);
      return [];
    } finally {
      useYouTubeStore.getState().setLoading(false);
    }
  }

  private fail(cause: unknown): void {
    this.toast("error", "toast.error", { message: failureMessage(cause, this.language()) });
  }

  private toast(
    kind: "info" | "success" | "error",
    key: MessageKey,
    params?: Record<string, string | number>,
  ): void {
    useToastStore.getState().push(kind, translate(this.language(), key, params));
  }
}
