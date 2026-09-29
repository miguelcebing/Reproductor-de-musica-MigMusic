/** Observable playlist collection (`PLAYLIST-001 = B`). */

import { create } from "zustand";

import type { Playlist } from "../domain/types";

export interface PlaylistStoreState {
  playlists: readonly Playlist[];
  activeId: string | null;
  loading: boolean;
  error: string | null;
  setPlaylists: (playlists: readonly Playlist[]) => void;
  upsertPlaylist: (playlist: Playlist) => void;
  dropPlaylist: (id: string) => void;
  setActiveId: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initial = {
  playlists: [] as readonly Playlist[],
  activeId: null as string | null,
  loading: false,
  error: null as string | null,
};

export const usePlaylistStore = create<PlaylistStoreState>((set) => ({
  ...initial,
  setPlaylists: (playlists) => set({ playlists }),
  upsertPlaylist: (playlist) =>
    set((state) => {
      const exists = state.playlists.some((item) => item.id === playlist.id);
      const playlists = exists
        ? state.playlists.map((item) => (item.id === playlist.id ? playlist : item))
        : [...state.playlists, playlist];
      return { playlists };
    }),
  dropPlaylist: (id) =>
    set((state) => ({
      playlists: state.playlists.filter((item) => item.id !== id),
      activeId: state.activeId === id ? null : state.activeId,
    })),
  setActiveId: (activeId) => set({ activeId }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({ ...initial }),
}));

/** The playlist currently shown in the list, if any. */
export function getActivePlaylist(state: {
  playlists: readonly Playlist[];
  activeId: string | null;
}): Playlist | null {
  if (state.activeId === null) return null;
  return state.playlists.find((playlist) => playlist.id === state.activeId) ?? null;
}
