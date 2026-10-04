/** Playlist use cases: orchestrate the API and the observable store.

 * Controllers own the application logic (POO, `SKILL5`): components call a
 * method and read the store, they never build URLs or handle errors.
 */

import { ApiError, ApiClient, failureMessage } from "./apiClient";
import { localSongFromFile } from "./localTracks";
import type { Playlist, Song, SongInput, TrackPosition } from "../domain/types";
import { usePlaylistStore } from "../state/playlistStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface PlaylistControllerOptions {
  /** Messages are rendered in the active language (`CONS-006`). */
  readonly language: () => Language;
  /** Optional playback controller to stop playback when playlist is deleted. */
  readonly playbackController?: { stop(): Promise<void> } | undefined;
}

export class PlaylistController {
  private readonly api: ApiClient;
  private readonly language: () => Language;
  private readonly playbackController: { stop(): Promise<void> } | undefined;

  constructor(api: ApiClient, options: PlaylistControllerOptions) {
    this.api = api;
    this.language = options.language;
    this.playbackController = options.playbackController;
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
      const activeId = usePlaylistStore.getState().activeId;
      const wasActive = activeId === id;
      await this.api.deletePlaylist(id);
      usePlaylistStore.getState().dropPlaylist(id);
      this.toast("success", "toast.deleted");
      if (wasActive && this.playbackController) {
        await this.playbackController.stop();
      }
      return true;
    } catch (cause) {
      this.fail(cause, "toast.error");
      return false;
    }
  }

  /** Add picked files as local tracks (`LOCAL-003`), honouring the position. */
  async addLocalTracks(
    playlistId: string,
    files: readonly File[],
    position: TrackPosition,
  ): Promise<Playlist | null> {
    if (files.length === 0) return null;
    const index =
      position.kind === "start" ? 0 : position.kind === "index" ? position.index : undefined;
    return this.mutate(
      async () => {
        // Metadata extraction stays per file (it reads each blob), but the
        // server call is batched: one read + one write instead of N of each.
        const songs = await Promise.all(files.map((file) => localSongFromFile(file)));
        return this.api.addSongs(playlistId, songs, index);
      },
      (playlist) => {
        usePlaylistStore.getState().upsertPlaylist(playlist);
        this.toast("success", "toast.added");
      },
    );
  }

  /** Add several catalog songs in one request, honouring the position (`F6`). */
  async addSongs(
    playlistId: string,
    songs: readonly SongInput[],
    position: TrackPosition,
  ): Promise<Playlist | null> {
    if (songs.length === 0) return null;
    const index =
      position.kind === "start" ? 0 : position.kind === "index" ? position.index : undefined;
    return this.mutate(
      () => this.api.addSongs(playlistId, songs, index),
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

  /** First index matching `text` (`FEAT-001-c`); `null` means "no matches". */
  async findFirst(playlistId: string, text: string): Promise<number | null> {
    if (text.trim().length === 0) return null;
    try {
      const found = await this.api.findSong(playlistId, text);
      return found.index;
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) return null;
      this.fail(cause, "toast.error");
      return null;
    }
  }

  /** Optimistic heart (`FEAT-001-b`); the server answer corrects the row. */
  async setFavorite(playlistId: string, index: number, favorite: boolean): Promise<Song | null> {
    const previous = this.patchSong(playlistId, index, (song) => ({ ...song, favorite }));
    if (!previous) return null;
    try {
      const updated = await this.api.setFavorite(playlistId, index, favorite);
      this.patchSong(playlistId, index, () => updated);
      return updated;
    } catch (cause) {
      this.patchSong(playlistId, index, () => previous);
      this.fail(cause, "toast.error");
      return null;
    }
  }

  /** Replace one song of a stored playlist, keeping every other reference. */
  private patchSong(
    playlistId: string,
    index: number,
    change: (song: Song) => Song,
  ): Song | null {
    const current = usePlaylistStore
      .getState()
      .playlists.find((playlist) => playlist.id === playlistId);
    if (!current) return null;
    const previous = current.songs[index];
    if (!previous) return null;
    const songs = [...current.songs];
    songs[index] = change(previous);
    usePlaylistStore.getState().upsertPlaylist({ ...current, songs });
    return previous;
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
    this.toast("error", fallback, { message: failureMessage(cause, this.language()) });
  }

  private toast(kind: "info" | "success" | "error", key: MessageKey, params?: Record<string, string | number>): void {
    useToastStore.getState().push(kind, translate(this.language(), key, params));
  }
}
