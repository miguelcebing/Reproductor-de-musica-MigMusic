/** Observable playback state. Logic lives in the controllers (`FRONT-005`). */

import { create } from "zustand";

import type { PlaybackState } from "../domain/types";

export interface PlaybackStoreState {
  playback: PlaybackState | null;
  setPlayback: (playback: PlaybackState | null) => void;
  reset: () => void;
}

export const usePlaybackStore = create<PlaybackStoreState>((set) => ({
  playback: null,
  setPlayback: (playback) => set({ playback }),
  reset: () => set({ playback: null }),
}));

/** Read the current transport state outside React (controllers, tests). */
export function getPlayback(): PlaybackState | null {
  return usePlaybackStore.getState().playback;
}
