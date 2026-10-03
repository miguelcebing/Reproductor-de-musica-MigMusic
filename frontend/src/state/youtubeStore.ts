/** YouTube Music catalog results shown while picking tracks (`F8`). */

import { create } from "zustand";

import type { Song } from "../domain/types";

export interface YouTubeStoreState {
  query: string;
  results: readonly Song[];
  loading: boolean;
  setQuery: (query: string) => void;
  setResults: (results: readonly Song[]) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useYouTubeStore = create<YouTubeStoreState>((set) => ({
  query: "",
  results: [],
  loading: false,
  setQuery: (query) => set({ query }),
  setResults: (results) => set({ results }),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ query: "", results: [], loading: false }),
}));
