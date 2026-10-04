import { describe, expect, it, vi } from "vitest";

import {
  ApiClient,
  ApiError,
  apiUrl,
  COLD_START_TIMEOUT_MS,
  failureMessage,
  REQUEST_TIMEOUT_MS,
  RETRY_BACKOFF_MS,
  resolveApiBaseUrl,
  type FetchLike,
} from "./apiClient";
describe("resolveApiBaseUrl", () => {
  it("appends /api to the given origin", () => {
    expect(resolveApiBaseUrl("https://migmusic.vercel.app")).toBe(
      "https://migmusic.vercel.app/api",
    );
  });

  it("tolerates origins with a trailing slash", () => {
    expect(resolveApiBaseUrl("http://127.0.0.1:5173/")).toBe(
      "http://127.0.0.1:5173/api",
    );
  });

  it("rejects an empty origin instead of producing a broken URL", () => {
    expect(() => resolveApiBaseUrl("")).toThrow(TypeError);
  });
});

describe("apiUrl", () => {
  it("joins base and path with a single slash", () => {
    expect(apiUrl("https://example.com/api", "/health")).toBe(
      "https://example.com/api/health",
    );
  });

  it("normalizes a path that does not start with a slash", () => {
    expect(apiUrl("https://example.com/api", "health")).toBe(
      "https://example.com/api/health",
    );
  });
});

/** Record every request and answer with a canned JSON body. */
interface RecordedCall {
  url: string;
  init?: RequestInit | undefined;
}

function recorder(status = 200, body: unknown = {}): {
  fetchImpl: FetchLike;
  calls: RecordedCall[];
} {
  const calls: RecordedCall[] = [];
  const fetchImpl: FetchLike = (url, init) => {
    calls.push({ url, init });
    return Promise.resolve(
      new Response(status === 204 ? null : JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      }),
    );
  };
  return { fetchImpl, calls };
}

describe("ApiClient Spotify auth", () => {
  const origin = "https://migmusic.example";

  it("builds the login URL on the API base", () => {
    const api = ApiClient.fromOrigin(origin, recorder().fetchImpl);
    expect(api.spotifyLoginUrl()).toBe(`${origin}/api/auth/spotify/login`);
  });

  it("reads the link status", async () => {
    const { fetchImpl, calls } = recorder(200, { authenticated: true });
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await expect(api.spotifyStatus()).resolves.toEqual({ authenticated: true });
    expect(calls[0]?.url).toBe(`${origin}/api/auth/spotify/status`);
    expect(calls[0]?.init?.method).toBe("GET");
  });

  it("posts the callback code and state", async () => {
    const { fetchImpl, calls } = recorder(200, { authenticated: true });
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.spotifyCallback("the-code", "the-state");
    expect(calls[0]?.init?.method).toBe("POST");
    expect(calls[0]?.url).toBe(`${origin}/api/auth/spotify/callback`);
    expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({
      code: "the-code",
      state: "the-state",
    });
  });

  it("requests a short-lived access token", async () => {
    const { fetchImpl, calls } = recorder(200, {
      access_token: "abc",
      expires_in: 60,
      token_type: "Bearer",
    });
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await expect(api.spotifyToken()).resolves.toMatchObject({ access_token: "abc" });
    expect(calls[0]?.url).toBe(`${origin}/api/auth/spotify/token`);
  });

  it("logs out with POST and no body", async () => {
    const { fetchImpl, calls } = recorder(204);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await expect(api.spotifyLogout()).resolves.toBeUndefined();
    expect(calls[0]?.init?.method).toBe("POST");
  });
});

describe("ApiClient Spotify catalog and player", () => {
  const origin = "https://migmusic.example";

  it("URL-encodes the search query", async () => {
    const { fetchImpl, calls } = recorder(200, []);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.searchSpotify("AC/DC & friends", 10);
    expect(calls[0]?.url).toBe(
      `${origin}/api/spotify/search?q=AC%2FDC%20%26%20friends&limit=10`,
    );
  });

  it("defaults the search page size to Spotify's limit of 10", async () => {
    const { fetchImpl, calls } = recorder(200, []);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.searchSpotify("night");
    expect(calls[0]?.url).toBe(`${origin}/api/spotify/search?q=night&limit=10`);
  });

  it("encodes the playlist id in the tracks route", async () => {
    const { fetchImpl, calls } = recorder(200, []);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.spotifyPlaylistTracks("pl/1");
    expect(calls[0]?.url).toContain("/api/spotify/playlists/pl%2F1/tracks");
  });

  it("sends the play body with device and uris", async () => {
    const { fetchImpl, calls } = recorder(204);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.spotifyPlay({ uris: ["spotify:track:1"], device_id: "dev", position_ms: 1500 });
    expect(calls[0]?.init?.method).toBe("PUT");
    expect(calls[0]?.url).toBe(`${origin}/api/spotify/player/play`);
    expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({
      uris: ["spotify:track:1"],
      device_id: "dev",
      position_ms: 1500,
    });
  });

  it("rounds and clamps the seek position", async () => {
    const { fetchImpl, calls } = recorder(204);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.spotifySeek(1234.6);
    expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({
      position_ms: 1235,
      device_id: undefined,
    });
  });

  it("clamps the volume to 0-100", async () => {
    const { fetchImpl, calls } = recorder(204);
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    await api.spotifySetVolume(150);
    await api.spotifySetVolume(-20);
    expect(JSON.parse(String(calls[0]?.init?.body))).toMatchObject({ volume_percent: 100 });
    expect(JSON.parse(String(calls[1]?.init?.body))).toMatchObject({ volume_percent: 0 });
  });

  it("reads the simplified player state", async () => {
    const { fetchImpl, calls } = recorder(200, {
      playing: true,
      position_ms: 10,
      duration_ms: 100,
      track_uri: "spotify:track:1",
      volume_percent: 50,
      device_id: "dev",
    });
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    const state = await api.spotifyPlayerState();
    expect(state.playing).toBe(true);
    expect(calls[0]?.url).toBe(`${origin}/api/spotify/player/state`);
  });
});

describe("ApiClient in-list search and favourites", () => {
  const origin = "https://migmusic.example";

  it("URL-encodes the find text and the playlist id", async () => {
    const { fetchImpl, calls } = recorder(200, { index: 1, song: {} });
    const api = ApiClient.fromOrigin(origin, fetchImpl);

    await api.findSong("pl 1", "hello world & more");

    expect(calls[0]?.init?.method).toBe("GET");
    expect(calls[0]?.url).toBe(
      `${origin}/api/playlists/pl%201/songs/find?text=hello+world+%26+more`,
    );
  });

  it("surfaces a 404 miss as an ApiError with the envelope code", async () => {
    const { fetchImpl } = recorder(404, {
      error: { code: "not_found", message: "No song matches", request_id: "req-1" },
    });
    const api = ApiClient.fromOrigin(origin, fetchImpl);

    await expect(api.findSong("pl-1", "zzz")).rejects.toMatchObject({
      status: 404,
      code: "not_found",
    });
  });

  it("PUTs the favourite flag as a boolean body", async () => {
    const { fetchImpl, calls } = recorder(200, { id: "local-1", favorite: true });
    const api = ApiClient.fromOrigin(origin, fetchImpl);

    await expect(api.setFavorite("pl-1", 2, true)).resolves.toMatchObject({ favorite: true });
    expect(calls[0]?.init?.method).toBe("PUT");
    expect(calls[0]?.url).toBe(`${origin}/api/playlists/pl-1/songs/2/favorite`);
    expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({ favorite: true });
  });
});

describe("ApiClient device scope header", () => {
  const origin = "https://migmusic.example";

  it("sends an ephemeral x-device-id when storage is unavailable", async () => {
    vi.stubGlobal("localStorage", undefined);
    try {
      const { fetchImpl, calls } = recorder(200, { authenticated: true });
      const api = ApiClient.fromOrigin(origin, fetchImpl);

      await api.spotifyStatus();

      const header = (calls[0]?.init?.headers as Record<string, string>)["x-device-id"];
      expect(header).toBeTruthy();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("tags every request with the stored device id", async () => {
    const values = new Map<string, string>([["mig_device_id", "device-a"]]);
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => void values.set(key, value),
    });
    try {
      const { fetchImpl, calls } = recorder(200, { authenticated: true });
      const api = ApiClient.fromOrigin(origin, fetchImpl);

      await api.spotifyStatus();

      expect((calls[0]?.init?.headers as Record<string, string>)["x-device-id"]).toBe("device-a");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("ApiClient request timeout", () => {
  const origin = "https://migmusic.example";

  it("aborts a hanging request and reports the timeout", async () => {
    vi.useFakeTimers();
    try {
      const fetchImpl: FetchLike = (_url, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("aborted", "AbortError")),
          );
        });
      const api = ApiClient.fromOrigin(origin, fetchImpl);

      // A read retries once and the extra attempt also hangs, so the request
      // only settles after every attempt's deadline has passed.
      const outcome = api.getPlayback().catch((cause: unknown) => cause);
      await vi.advanceTimersByTimeAsync(COLD_START_TIMEOUT_MS + 1);
      await vi.advanceTimersByTimeAsync(RETRY_BACKOFF_MS + REQUEST_TIMEOUT_MS + 1);
      const error = await outcome;

      expect(error).toBeInstanceOf(ApiError);
      expect(error).toMatchObject({ status: 0, code: "timeout" });
    } finally {
      vi.useRealTimers();
    }
  });

  it("clears the abort timer once the answer lands", async () => {
    vi.useFakeTimers();
    try {
      let signal: AbortSignal | undefined;
      const fetchImpl: FetchLike = (_url, init) => {
        signal = init?.signal ?? undefined;
        return Promise.resolve(
          new Response(JSON.stringify({ authenticated: true }), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        );
      };
      const api = ApiClient.fromOrigin(origin, fetchImpl);

      await api.spotifyStatus();
      await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS * 2);

      expect(signal?.aborted).toBe(false);
    } finally {
      vi.useRealTimers();
    }
  });

  it("reports a caller-cancelled request as aborted, not as a timeout", async () => {
    const fetchImpl: FetchLike = (_url, init) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () =>
          reject(new DOMException("aborted", "AbortError")),
        );
      });
    const api = ApiClient.fromOrigin(origin, fetchImpl);
    const controller = new AbortController();

    const outcome = api.selectSong("pl-1", 0, controller.signal).catch((cause: unknown) => cause);
    controller.abort();
    const error = await outcome;

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 0, code: "aborted" });
  });
});

describe("failureMessage", () => {
  it("localises the timeout copy", () => {
    const error = new ApiError(0, "timeout", "request timed out");
    expect(failureMessage(error, "es")).toBe("El servidor tardó demasiado en responder");
    expect(failureMessage(error, "en")).toBe("The server took too long to respond");
  });

  it("keeps every other message untouched", () => {
    expect(failureMessage(new ApiError(404, "not_found", "No song matches"), "es")).toBe(
      "No song matches",
    );
    expect(failureMessage(new Error("offline"), "es")).toBe("offline");
    expect(failureMessage("plain text", "es")).toBe("plain text");
  });
});

describe("ApiClient cold-start resilience", () => {
  const origin = "https://migmusic.example";

  it("retries a GET once after a gateway error and succeeds", async () => {
    let attempts = 0;
    const fetchImpl: FetchLike = () => {
      attempts += 1;
      if (attempts === 1) {
        return Promise.resolve(new Response("booting", { status: 503 }));
      }
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );
    };
    const api = ApiClient.fromOrigin(origin, fetchImpl);

    const result = await api.searchSpotify("night");

    expect(result).toEqual([]);
    expect(attempts).toBe(2);
  });

  it("does not retry a write (POST) on a gateway error", async () => {
    let attempts = 0;
    const fetchImpl: FetchLike = () => {
      attempts += 1;
      return Promise.resolve(new Response("down", { status: 503 }));
    };
    const api = ApiClient.fromOrigin(origin, fetchImpl);

    await expect(api.createPlaylist("Mix")).rejects.toMatchObject({ status: 503 });
    expect(attempts).toBe(1);
  });

  it("does not retry a real 4xx refusal", async () => {
    let attempts = 0;
    const fetchImpl: FetchLike = () => {
      attempts += 1;
      return Promise.resolve(
        new Response(JSON.stringify({ error: { code: "bad_request", message: "no" } }), {
          status: 400,
          headers: { "content-type": "application/json" },
        }),
      );
    };
    const api = ApiClient.fromOrigin(origin, fetchImpl);

    await expect(api.searchYouTube("x")).rejects.toMatchObject({ status: 400 });
    expect(attempts).toBe(1);
  });
});
