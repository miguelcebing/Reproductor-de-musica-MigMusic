/** Observable playback state. Logic lives in the controllers (`FRONT-005`). */

import { create } from "zustand";

import type { PlaybackState } from "../domain/types";
import { withLiveArtwork } from "../services/localFileUrls";

export interface PlaybackStoreState {
  playback: PlaybackState | null;
  setPlayback: (playback: PlaybackState | null) => void;
  reset: () => void;
}

export const usePlaybackStore = create<PlaybackStoreState>((set) => ({
  playback: null,
  setPlayback: (playback) =>
    set({
      playback:
        playback && playback.song
          ? { ...playback, song: withLiveArtwork(playback.song) }
          : playback,
    }),
  reset: () => set({ playback: null }),
}));
