/** Whether this browser session is linked to Spotify (`SPOTIFY-007`). */

import { create } from "zustand";

/** `unknown` until the first status check; `checking` while it is in flight. */
export type SpotifyLinkStatus = "unknown" | "checking" | "linked" | "anonymous";

export interface AuthStoreState {
  status: SpotifyLinkStatus;
  setStatus: (status: SpotifyLinkStatus) => void;
  reset: () => void;
}

export const useAuthStore = create<AuthStoreState>((set) => ({
  status: "unknown",
  setStatus: (status) => set({ status }),
  reset: () => set({ status: "unknown" }),
}));
