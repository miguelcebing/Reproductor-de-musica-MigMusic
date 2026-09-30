import { beforeEach, describe, expect, it } from "vitest";

import { ApiClient, type FetchLike } from "./apiClient";
import { PlaylistController } from "./PlaylistController";
import { usePlaylistStore } from "../state/playlistStore";
import { useToastStore } from "../state/toastStore";
import type { Playlist, Song } from "../domain/types";

// --- fixtures ---------------------------------------------------------------

function makeSong(index: number, overrides: Partial<Song> = {}): Song {
  return {
    id: `local-${index}`,
    title: `Song ${index}`,
    artist: "MigMusic",
    source: "local",
    duration: 180,
    duration_label: "3:00",
    album: null,
    artwork_url: null,
    external_url: null,
    available: true,
    favorite: false,
    ...overrides,
  };
}

function makePlaylist(): Playlist {
  return {
    id: "pl-1",
    name: "Road trip",
    size: 3,
    current_index: 0,
    songs: [makeSong(0), makeSong(1), makeSong(2)],
  };
}

/** Controller wired to a canned handler; records every request URL. */
function controllerWith(handler: (url: string, init?: RequestInit) => { status: number; body: unknown }): {
  controller: PlaylistController;
  calls: { url: string; init?: RequestInit | undefined }[];
} {
  const calls: { url: string; init?: RequestInit | undefined }[] = [];
  const fetchImpl: FetchLike = (url, init) => {
    calls.push({ url, init });
    const { status, body } = handler(url, init);
    return Promise.resolve(
      new Response(status === 204 ? null : JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      }),
    );
  };
  const controller = new PlaylistController(ApiClient.fromOrigin("https://app.test", fetchImpl), {
    language: () => "es",
  });
  return { controller, calls };
}

function seedStore(playlist: Playlist = makePlaylist()): void {
  usePlaylistStore.getState().setPlaylists([playlist]);
  usePlaylistStore.getState().setActiveId(playlist.id);
}

function storedSong(index: number): Song | undefined {
  const store = usePlaylistStore.getState();
  return store.playlists.find((playlist) => playlist.id === "pl-1")?.songs[index];
}

beforeEach(() => {
  usePlaylistStore.getState().reset();
  useToastStore.getState().reset();
});

// --- findFirst (`FEAT-001-c`) -----------------------------------------------

describe("PlaylistController.findFirst", () => {
  it("returns the index of the first match", async () => {
    seedStore();
    const { controller } = controllerWith(() => ({
      status: 200,
      body: { index: 1, song: makeSong(1) },
    }));

    await expect(controller.findFirst("pl-1", "song 2")).resolves.toBe(1);
  });

  it("answers null on a quiet 404 miss, without toasting", async () => {
    seedStore();
    const { controller } = controllerWith(() => ({
      status: 404,
      body: { error: { code: "not_found", message: "nope", request_id: "r" } },
    }));

    await expect(controller.findFirst("pl-1", "zzz")).resolves.toBeNull();
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("skips the network entirely for blank text", async () => {
    seedStore();
    const { controller, calls } = controllerWith(() => {
      throw new Error("should not be called");
    });

    await expect(controller.findFirst("pl-1", "   ")).resolves.toBeNull();
    expect(calls).toHaveLength(0);
  });

  it("toasts unexpected failures", async () => {
    seedStore();
    const { controller } = controllerWith(() => ({
      status: 500,
      body: { error: { code: "internal_error", message: "boom", request_id: "r" } },
    }));

    await expect(controller.findFirst("pl-1", "song")).resolves.toBeNull();
    expect(useToastStore.getState().toasts[0]?.kind).toBe("error");
  });
});

// --- setFavorite (`FEAT-001-b`) ---------------------------------------------

describe("PlaylistController.setFavorite", () => {
  it("marks the row and keeps the server answer", async () => {
    seedStore();
    const { controller, calls } = controllerWith(() => ({
      status: 200,
      body: makeSong(1, { favorite: true }),
    }));

    const updated = await controller.setFavorite("pl-1", 1, true);

    expect(updated?.favorite).toBe(true);
    expect(storedSong(1)?.favorite).toBe(true);
    expect(storedSong(0)?.favorite).toBe(false);
    expect(calls[0]?.url).toContain("/songs/1/favorite");
  });

  it("clears the heart again (idempotent flag)", async () => {
    seedStore(makePlaylist());
    usePlaylistStore.getState().upsertPlaylist({
      ...makePlaylist(),
      songs: [makeSong(0), makeSong(1, { favorite: true }), makeSong(2)],
    });
    const { controller } = controllerWith(() => ({
      status: 200,
      body: makeSong(1, { favorite: false }),
    }));

    await controller.setFavorite("pl-1", 1, false);

    expect(storedSong(1)?.favorite).toBe(false);
  });

  it("reverts the optimistic row and toasts when the API fails", async () => {
    seedStore();
    const { controller } = controllerWith(() => ({
      status: 500,
      body: { error: { code: "internal_error", message: "boom", request_id: "r" } },
    }));

    const updated = await controller.setFavorite("pl-1", 0, true);

    expect(updated).toBeNull();
    expect(storedSong(0)?.favorite).toBe(false); // rolled back
    expect(useToastStore.getState().toasts[0]?.kind).toBe("error");
  });

  it("does nothing for an index outside the list", async () => {
    seedStore();
    const { controller, calls } = controllerWith(() => {
      throw new Error("should not be called");
    });

    await expect(controller.setFavorite("pl-1", 9, true)).resolves.toBeNull();
    expect(calls).toHaveLength(0);
  });
});
