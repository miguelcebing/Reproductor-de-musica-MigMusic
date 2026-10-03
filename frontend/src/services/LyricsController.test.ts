import { afterEach, describe, expect, it, vi } from "vitest";

import { LyricsController } from "./LyricsController";
import { ApiError, type ApiClient } from "./apiClient";
import type { Lyrics, Song } from "../domain/types";
import { useToastStore } from "../state/toastStore";

function makeSong(id = "abc123"): Song {
  return {
    id,
    title: "Song",
    artist: "Artist",
    source: "youtube",
    duration: 200,
    duration_label: "3:20",
    album: null,
    artwork_url: null,
    external_url: null,
    available: true,
    favorite: false,
  };
}

function makeClient(getLyrics: (query: unknown) => Promise<Lyrics | null>) {
  return { getLyrics } as unknown as ApiClient;
}

afterEach(() => {
  LyricsController.clearCache();
  useToastStore.getState().reset();
});

describe("LyricsController", () => {
  it("returns the lyrics the API found", async () => {
    const getLyrics = vi.fn().mockResolvedValue({ text: "La", source: "lrclib", synced: false });
    const controller = new LyricsController(makeClient(getLyrics), { language: () => "en" });

    const result = await controller.forSong(makeSong());

    expect(result).toEqual({ status: "ok", lyrics: { text: "La", source: "lrclib", synced: false } });
    expect(getLyrics).toHaveBeenCalledTimes(1);
  });

  it("maps a 204 (null) to the empty state", async () => {
    const controller = new LyricsController(makeClient(vi.fn().mockResolvedValue(null)), {
      language: () => "en",
    });

    expect(await controller.forSong(makeSong())).toEqual({ status: "empty" });
  });

  it("caches a settled result so a song is never asked twice", async () => {
    const getLyrics = vi.fn().mockResolvedValue(null);
    const controller = new LyricsController(makeClient(getLyrics), { language: () => "en" });
    const song = makeSong();

    await controller.forSong(song);
    await controller.forSong(song);

    expect(getLyrics).toHaveBeenCalledTimes(1);
  });

  it("reports a failure without throwing and caches it", async () => {
    const getLyrics = vi.fn().mockRejectedValue(new ApiError(504, "upstream_error", "down"));
    const controller = new LyricsController(makeClient(getLyrics), { language: () => "en" });
    const song = makeSong();

    expect(await controller.forSong(song)).toEqual({ status: "error" });
    await controller.forSong(song);
    expect(getLyrics).toHaveBeenCalledTimes(1);
    expect(useToastStore.getState().toasts).toHaveLength(1);
  });
});
