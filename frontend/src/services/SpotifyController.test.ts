import { beforeEach, describe, expect, it } from "vitest";

import { ApiClient, type FetchLike } from "./apiClient";
import { SpotifyController } from "./SpotifyController";
import { useSpotifyStore } from "../state/spotifyStore";
import { useToastStore } from "../state/toastStore";
import type { Song } from "../domain/types";

function song(id: string): Song {
  return {
    id,
    title: `Track ${id}`,
    artist: "Artist",
    source: "spotify",
    duration: 180,
    duration_label: "3:00",
    album: null,
    artwork_url: null,
    external_url: null,
    available: true,
    favorite: false,
  };
}

function controllerWith(handler: (url: string) => { status: number; body: unknown }): SpotifyController {
  const fetchImpl: FetchLike = (url) => {
    const { status, body } = handler(url);
    return Promise.resolve(
      new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      }),
    );
  };
  return new SpotifyController(ApiClient.fromOrigin("https://app.test", fetchImpl), {
    language: () => "es",
  });
}

beforeEach(() => {
  useSpotifyStore.getState().reset();
  useToastStore.getState().reset();
});

describe("SpotifyController", () => {
  it("publishes search results and the query", async () => {
    const controller = controllerWith(() => ({ status: 200, body: [song("a"), song("b")] }));
    const results = await controller.search("  hello  ");

    expect(results.map((s) => s.id)).toEqual(["a", "b"]);
    expect(useSpotifyStore.getState().results).toHaveLength(2);
    expect(useSpotifyStore.getState().query).toBe("  hello  ");
    expect(useSpotifyStore.getState().loading).toBe(false);
  });

  it("short-circuits an empty query without hitting the API", async () => {
    const controller = controllerWith(() => {
      throw new Error("should not be called");
    });
    await expect(controller.search("   ")).resolves.toEqual([]);
    expect(useSpotifyStore.getState().results).toEqual([]);
    expect(useSpotifyStore.getState().loading).toBe(false);
  });

  it("toasts the empty-result case", async () => {
    const controller = controllerWith(() => ({ status: 200, body: [] }));
    await controller.search("nothing");
    expect(useToastStore.getState().toasts[0]?.kind).toBe("info");
  });

  it("toasts and clears the list when the search fails", async () => {
    const failing = controllerWith(() => {
      throw new Error("offline");
    });
    // A throwing fetch becomes a network error envelope inside ApiClient.
    const results = await failing.search("anything");
    expect(results).toEqual([]);
    expect(useSpotifyStore.getState().results).toEqual([]);
    expect(useSpotifyStore.getState().loading).toBe(false);
    expect(useToastStore.getState().toasts[0]?.kind).toBe("error");
  });

  it("stores the linked account playlists", async () => {
    const controller = controllerWith(() => ({
      status: 200,
      body: [{ id: "p1", name: "Mix", track_count: 10, artwork_url: null }],
    }));
    const playlists = await controller.loadPlaylists();
    expect(playlists[0]?.name).toBe("Mix");
    expect(useSpotifyStore.getState().playlists).toHaveLength(1);
  });
});
