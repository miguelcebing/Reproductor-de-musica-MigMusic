/** User interface preferences: theme (`VIS-002`) and language (`CONS-006`). */

import { create } from "zustand";

import type { Language } from "../i18n/messages";

export type Theme = "dark" | "light";

export interface SettingsStoreState {
  theme: Theme;
  language: Language;
  volume: number;
  muted: boolean;
  setTheme: (theme: Theme) => void;
  setLanguage: (language: Language) => void;
  setVolume: (volume: number) => void;
  setMuted: (muted: boolean) => void;
  reset: () => void;
}

const STORAGE_KEY = "migmusic.settings";

interface StoredSettings {
  theme?: Theme;
  language?: Language;
  volume?: number;
  muted?: boolean;
}

function readStored(): StoredSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredSettings) : {};
  } catch {
    return {};
  }
}

function writeStored(settings: StoredSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Private mode or quota exceeded: preferences simply do not persist.
  }
}

const stored = readStored();

/** Mirror the preferences onto `<html>` so CSS variables can react. */
export function applyDocumentSettings(theme: Theme, language: Language): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
  document.documentElement.lang = language;
}

export const useSettingsStore = create<SettingsStoreState>((set, get) => ({
  theme: stored.theme === "light" ? "light" : "dark",
  language: stored.language === "en" ? "en" : "es",
  volume: typeof stored.volume === "number" ? clamp(stored.volume) : 0.8,
  muted: stored.muted === true,
  setTheme: (theme) => {
    set({ theme });
    persist(get());
  },
  setLanguage: (language) => {
    set({ language });
    persist(get());
  },
  setVolume: (volume) => {
    set({ volume: clamp(volume), muted: volume === 0 });
    persist(get());
  },
  setMuted: (muted) => {
    set({ muted });
    persist(get());
  },
  reset: () => set({ theme: "dark", language: "es", volume: 0.8, muted: false }),
}));

function clamp(volume: number): number {
  if (Number.isNaN(volume)) return 0;
  return Math.min(1, Math.max(0, volume));
}

function persist(state: SettingsStoreState): void {
  applyDocumentSettings(state.theme, state.language);
  writeStored({
    theme: state.theme,
    language: state.language,
    volume: state.volume,
    muted: state.muted,
  });
}
