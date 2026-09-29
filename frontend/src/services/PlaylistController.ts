/** Playlist use cases: orchestrate the API and the observable store.

 * Controllers own the application logic (POO, `SKILL5`): components call a
 * method and read the store, they never build URLs or handle errors.
 */

import { ApiError, ApiClient } from "./apiClient";
import { localSongFromFile } from "./localTracks";
import type { Playlist, SongInput, TrackPosition } from "../domain/types";
import { usePlaylistStore } from "../state/playlistStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface PlaylistControllerOptions {
  /** Messages are rendered in the active language (`CONS-006`). */
  readonly language: () => Language;
}

export class PlaylistController {
  private readonly api: ApiClient;
  private readonly language: () => Language;

  constructor(api: ApiClient, options: PlaylistControllerOptions) {
    this.api = api;
    this.language = options.language;
  }

  async refresh(): Promise<readonly Playlist[] | null> {
    const store = usePlaylistStore.getState();
    store.setLoading(true);
    store.setError(null);
    try {
      const playlists = await this.api.listPlaylists();
      usePlaylistStore.getState().setPlaylists(playlists);
      const activeId = usePlaylistStore.getState().activeId;
      const stillExists = activeId !== null && playlists.some((p) => p.id === activeId);
      if (!stillExists) {
        usePlaylistStore.getState().setActiveId(playlists[0]?.id ?? null);
      }
      return playlists;
    } catch (cause) {
      this.fail(cause, "state.offline");
      return null;
    } finally {
      usePlaylistStore.getState().setLoading(false);
    }
  }

  async create(name: string): Promise<Playlist | null> {
    return this.mutate(
      () => this.api.createPlaylist(name),
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        usePlaylistStore.getState().setActiveId(playlist.id);
        this.toast("success", "toast.created");
      },
    );
  }

  async rename(id: string, name: string): Promise<Playlist | null> {
    return this.mutate(
      () => this.api.renamePlaylist(id, name),
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        this.toast("success", "toast.renamed");
      },
    );
  }

  async remove(id: string): Promise<boolean> {
    try {
      await this.api.deletePlaylist(id);
      usePlaylistStore.getState().dropPlaylist(id);
      this.toast("success", "toast.deleted");
      return true;
    } catch (cause) {
      this.fail(cause, "toast.error");
      return false;
    }
  }

  async addSong(playlistId: string, song: SongInput, index?: number): Promise<Playlist | null> {
    return this.mutate(
      () => this.api.addSong(playlistId, song, index),
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        this.toast("success", "toast.added");
      },
    );
  }

  /** Add picked files as local tracks (`LOCAL-001`), honouring the position. */
  async addLocalTracks(
    playlistId: string,
    files: readonly File[],
    position: TrackPosition,
  ): Promise<Playlist | null> {
    if (files.length === 0) return null;
    return this.mutate(
      async () => {
        let index =
          position.kind === "start" ? 0 : position.kind === "index" ? position.index : undefined;
        for (const file of files) {
          await this.api.addSong(playlistId, localSongFromFile(file), index);
          if (index !== undefined) index += 1;
        }
        return this.api.getPlaylist(playlistId);
      },
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        this.toast("success", "toast.added");
      },
    );
  }

  async removeSong(playlistId: string, index: number): Promise<Playlist | null> {
    return this.mutate(
      async () => {
        await this.api.removeSong(playlistId, index);
        return this.api.getPlaylist(playlistId);
      },
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        this.toast("success", "toast.removed");
      },
    );
  }

  async moveSong(playlistId: string, fromIndex: number, toIndex: number): Promise<Playlist | null> {
    if (fromIndex === toIndex) return null;
    const current = usePlaylistStore
      .getState()
      .playlists.find((playlist) => playlist.id === playlistId);
    if (!current) return null;

    // Optimistic reorder so dragging feels instant; the API answer wins after.
    const songs = [...current.songs];
    const [moved] = songs.splice(fromIndex, 1);
    if (!moved) return null;
    songs.splice(toIndex, 0, moved);
    usePlaylistStore.getState().upsertPlaylist({ ...current, songs });

    return this.mutate(
      () => this.api.moveSong(playlistId, fromIndex, toIndex),
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        this.toast("success", "toast.moved");
      },
    );
  }

  private async mutate<T>(
    request: () => Promise<T>,
    onSuccess: (result: T) => void,
  ): Promise<T | null> {
    try {
      const result = await request();
      onSuccess(result);
      return result;
    } catch (cause) {
      this.fail(cause, "toast.error");
      return null;
    }
  }

  private fail(cause: unknown, fallback: MessageKey): void {
    const message =
      cause instanceof ApiError
        ? cause.message
        : cause instanceof Error
          ? cause.message
          : String(cause);
    this.toast("error", fallback, { message });
  }

  private toast(kind: "info" | "success" | "error", key: MessageKey, params?: Record<string, string | number>): void {
    useToastStore.getState().push(kind, translate(this.language(), key, params));
  }
}
