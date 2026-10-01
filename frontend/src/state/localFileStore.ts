/** Which local tracks still have their bytes on this device (`LOCAL-006`).

 * IndexedDB is per-origin and per-browser: clearing site data (or a record
 * written before blob persistence) leaves a track in the queue without a file.
 * Those ids are remembered here so the row can offer to re-link the file.
 */

import { create } from "zustand";

export interface LocalFileStoreState {
  /** Track ids whose audio bytes are missing on this device. */
  missing: readonly string[];
  setMissing: (ids: readonly string[]) => void;
  markMissing: (id: string) => void;
  markPresent: (id: string) => void;
  reset: () => void;
}

export const useLocalFileStore = create<LocalFileStoreState>((set) => ({
  missing: [],
  setMissing: (ids) => set({ missing: [...ids] }),
  markMissing: (id) =>
    set((state) =>
      state.missing.includes(id) ? state : { missing: [...state.missing, id] },
    ),
  markPresent: (id) =>
    set((state) => ({ missing: state.missing.filter((tracked) => tracked !== id) })),
  reset: () => set({ missing: [] }),
}));
