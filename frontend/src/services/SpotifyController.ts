/** Spotify catalog use cases: search results land in the observable store.

 * Components never call the API: they ask the controller for a query and
 * read `useSpotifyStore` (`SKILL5`, POO).
 */

import { ApiClient, failureMessage } from "./apiClient";
import type { Song, SpotifyPlaylist } from "../domain/types";
import { useSpotifyStore } from "../state/spotifyStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface SpotifyControllerOptions {
  readonly language: () => Language;
}

export class SpotifyController {
  private readonly api: ApiClient;
  private readonly language: () => Language;

  constructor(api: ApiClient, options: SpotifyControllerOptions) {
    this.api = api;
    this.language = options.language;
  }

  /** Search Spotify and publish the (possibly empty) result list. */
  async search(query: string): Promise<readonly Song[]> {
    const trimmed = query.trim();
    const store = useSpotifyStore.getState();
    store.setQuery(query);
    if (trimmed.length === 0) {
      store.setResults([]);
      return [];
    }
    store.setLoading(true);
    try {
      const results = await this.api.searchSpotify(trimmed);
      useSpotifyStore.getState().setResults(results);
      if (results.length === 0) this.toast("info", "spotify.noResults");
      return results;
    } catch (cause) {
      this.fail(cause);
      useSpotifyStore.getState().setResults([]);
      return [];
    } finally {
      useSpotifyStore.getState().setLoading(false);
    }
  }

  /** List the linked account's playlists (`playlist-read-private`). */
  async loadPlaylists(): Promise<readonly SpotifyPlaylist[]> {
    try {
      const playlists = await this.api.listSpotifyPlaylists();
      useSpotifyStore.getState().setPlaylists(playlists);
      return playlists;
    } catch (cause) {
      this.fail(cause);
      return [];
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
