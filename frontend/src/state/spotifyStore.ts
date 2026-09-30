/** Spotify catalog results shown while picking tracks (`SPOTIFY-006`). */

import { create } from "zustand";

import type { Song, SpotifyPlaylist } from "../domain/types";

export interface SpotifyStoreState {
  query: string;
  results: readonly Song[];
  playlists: readonly SpotifyPlaylist[];
  loading: boolean;
  setQuery: (query: string) => void;
  setResults: (results: readonly Song[]) => void;
  setPlaylists: (playlists: readonly SpotifyPlaylist[]) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useSpotifyStore = create<SpotifyStoreState>((set) => ({
  query: "",
  results: [],
  playlists: [],
  loading: false,
  setQuery: (query) => set({ query }),
  setResults: (results) => set({ results }),
  setPlaylists: (playlists) => set({ playlists }),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ query: "", results: [], playlists: [], loading: false }),
}));
