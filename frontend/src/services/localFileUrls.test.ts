import { beforeAll, beforeEach, afterAll, describe, expect, it, vi } from "vitest";

import type { Playlist } from "../domain/types";

const hoisted = vi.hoisted(() => ({
  tracks: [] as Array<Record<string, unknown>>,
  blobs: new Map<string, Blob>(),
}));

vi.mock("../storage/LocalLibraryRepository", () => ({
  localLibrary: {
    getAll: async () => hoisted.tracks,
    getBlob: async (id: string) => hoisted.blobs.get(id),
    put: async () => undefined,
    relink: async () => undefined,
    markUnavailable: async () => undefined,
    remove: async () => undefined,
    clear: async () => undefined,
  },
}));

import {
  clearAllObjectUrls,
  localArtworkUrls,
  localFileUrls,
  restoreObjectUrlsFromIndexedDB,
  withLiveArtwork,
  withLiveArtworkIn,
} from "./localFileUrls";

let urlSeq = 0;
const originalCreate = URL.createObjectURL;
const originalRevoke = URL.revokeObjectURL;

beforeAll(() => {
  URL.createObjectURL = () => `blob:test/${++urlSeq}`;
  URL.revokeObjectURL = () => undefined;
});

afterAll(() => {
  URL.createObjectURL = originalCreate;
  URL.revokeObjectURL = originalRevoke;
});

beforeEach(() => {
  clearAllObjectUrls();
  hoisted.tracks = [];
  hoisted.blobs.clear();
});

describe("restoreObjectUrlsFromIndexedDB (LOCAL-006)", () => {
  it("rebuilds audio urls and reports the tracks whose bytes are gone", async () => {
    hoisted.tracks = [
      { id: "local:a", blob: new Blob(["audio"]), artwork_url: null },
      { id: "local:b", artwork_url: "blob:dead" }, // legacy record: no bytes
    ];

    const report = await restoreObjectUrlsFromIndexedDB();

    expect(report.restored).toBe(1);
    expect(report.missing).toEqual(["local:b"]);
    expect(localFileUrls.get("local:a")).toMatch(/^blob:/);
    expect(localFileUrls.has("local:b")).toBe(false);
  });

  it("rebuilds the artwork url from the stored blob", async () => {
    hoisted.tracks = [
      {
        id: "local:c",
        blob: new Blob(["audio"]),
        artworkBlob: new Blob(["cover"]),
        artwork_url: "blob:dead-artwork",
      },
    ];

    await restoreObjectUrlsFromIndexedDB();

    const fresh = localArtworkUrls.get("local:c");
    expect(fresh).toMatch(/^blob:/);
    expect(fresh).not.toBe("blob:dead-artwork");
  });
});

describe("withLiveArtwork", () => {
  it("swaps a dead blob url for the rebuilt one", async () => {
    hoisted.tracks = [
      {
        id: "local:c",
        blob: new Blob(["audio"]),
        artworkBlob: new Blob(["cover"]),
        artwork_url: "blob:dead-artwork",
      },
    ];
    await restoreObjectUrlsFromIndexedDB();

    const hydrated = withLiveArtwork({ id: "local:c", artwork_url: "blob:dead-artwork" });

    expect(hydrated.artwork_url).toBe(localArtworkUrls.get("local:c"));
    expect(withLiveArtwork(hydrated)).toBe(hydrated); // idempotent
  });

  it("falls back to no artwork when the bytes are gone", () => {
    expect(withLiveArtwork({ id: "local:x", artwork_url: "blob:dead" }).artwork_url).toBeNull();
  });

  it("leaves remote artwork alone", () => {
    const song = { id: "abc", artwork_url: "https://i.scdn.co/image/x" };
    expect(withLiveArtwork(song)).toBe(song);
  });
});

describe("withLiveArtworkIn", () => {
  const song = (id: string, artwork_url: string | null) => ({
    id,
    title: id,
    artist: "a",
    source: "local" as const,
    duration: 1,
    duration_label: "0:01",
    album: null,
    artwork_url,
    external_url: null,
    available: true,
    favorite: false,
  });

  const playlist = (songs: ReturnType<typeof song>[]): Playlist => ({
    id: "pl-1",
    name: "mix",
    size: songs.length,
    current_index: null,
    songs,
  });

  it("keeps the playlist untouched when no artwork is a dead blob", () => {
    const list = playlist([song("local:a", null), song("abc", "https://img")]);
    expect(withLiveArtworkIn(list)).toBe(list);
  });

  it("hydrates every dead artwork url", async () => {
    hoisted.tracks = [
      {
        id: "local:a",
        blob: new Blob(["audio"]),
        artworkBlob: new Blob(["cover"]),
        artwork_url: "blob:dead-a",
      },
    ];
    await restoreObjectUrlsFromIndexedDB();

    const list = playlist([song("local:a", "blob:dead-a"), song("abc", "https://img")]);
    const hydrated = withLiveArtworkIn(list);

    expect(hydrated.songs[0].artwork_url).toBe(localArtworkUrls.get("local:a"));
    expect(hydrated.songs[1].artwork_url).toBe("https://img");
  });
});
