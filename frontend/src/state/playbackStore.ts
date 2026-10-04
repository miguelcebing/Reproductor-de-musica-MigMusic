/** Observable playback state. Logic lives in the controllers (`FRONT-005`). */

import { create } from "zustand";

import type { PlaybackState } from "../domain/types";
import { withLiveArtwork } from "../services/localFileUrls";

export interface PlaybackStoreState {
  playback: PlaybackState | null;
  /** A track was picked and its audio is still being prepared (`F12`). */
  loading: boolean;
  setPlayback: (playback: PlaybackState | null) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const usePlaybackStore = create<PlaybackStoreState>((set) => ({
  playback: null,
  loading: false,
  setPlayback: (playback) =>
    set({
      playback:
        playback && playback.song
          ? { ...playback, song: withLiveArtwork(playback.song) }
          : playback,
    }),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ playback: null, loading: false }),
}));
