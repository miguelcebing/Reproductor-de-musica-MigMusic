import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PlaybackController } from "./PlaybackController";
import { ApiError, type ApiClient } from "./apiClient";
import type {
  AudioSource,
  PlaybackState,
  RepeatMode,
  SkipDirection,
  Song,
} from "../domain/types";
import type { AudioPlayer, PlayerEventType, PlayerEventListener } from "../players/AudioPlayer";
import { usePlaybackStore } from "../state/playbackStore";
import { usePlaylistStore } from "../state/playlistStore";
import { useSettingsStore } from "../state/settingsStore";
import { useToastStore } from "../state/toastStore";
import { useLocalFileStore } from "../state/localFileStore";

// --- fixtures ---------------------------------------------------------------

function makeSong(id: string, source: AudioSource = "local"): Song {
  return {
    id,
    title: id,
    artist: "Artist",
    source,
    duration: 200,
    duration_label: "3:20",
    album: null,
    artwork_url: null,
    external_url: null,
    available: true,
    favorite: false,
  };
}

function makeState(overrides: Partial<PlaybackState> = {}): PlaybackState {
  return {
    playlist_id: "pl-1",
    song: makeSong("local:1"),
    index: 0,
    position: 0,
    playing: true,
    repeat: "off" as RepeatMode,
    shuffle: false,
    size: 2,
    available_next: true,
    available_previous: false,
    next_index: 1,
    previous_index: null,
    skip_seconds: 5,
    ...overrides,
  };
}

/** Fake `AudioPlayer` that records every call and can replay events. */
class FakePlayer implements AudioPlayer {
  source = "";
  isPlaying = false;
  currentTime = 0;
  duration = 200;
  volume = 1;
  muted = false;
  destroyed = false;
  loadedWith: { source: string; startTime?: number } | null = null;
  playCalls = 0;
  pauseCalls = 0;
  seekCalls: number[] = [];
  volumeCalls: number[] = [];
  private readonly listeners = new Map<PlayerEventType, Set<PlayerEventListener>>();

  constructor(
    readonly kind: AudioSource,
    private readonly failLoad = false,
    private readonly failMessage = "boom",
    private readonly failPlay: { message: string; name?: string } | null = null,
    private readonly gatePlay: Promise<void> | null = null,
  ) {}

  async load(source: string, options?: { startTime?: number }): Promise<void> {
    if (this.failLoad) throw new Error(this.failMessage);
    this.source = source;
    this.loadedWith =
      options?.startTime !== undefined ? { source, startTime: options.startTime } : { source };
  }

  async play(): Promise<void> {
    this.playCalls += 1;
    if (this.gatePlay) await this.gatePlay;
    if (this.failPlay) {
      const error = new Error(this.failPlay.message);
      if (this.failPlay.name) error.name = this.failPlay.name;
      throw error;
    }
    this.isPlaying = true;
  }

  pause(): void {
    this.pauseCalls += 1;
    this.isPlaying = false;
  }

  async seek(time: number): Promise<void> {
    this.seekCalls.push(time);
    this.currentTime = time;
  }

  setVolume(volume: number): void {
    this.volume = volume;
    this.volumeCalls.push(volume);
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
  }

  destroy(): void {
    this.destroyed = true;
  }

  on(event: PlayerEventType, listener: PlayerEventListener): () => void {
    const group = this.listeners.get(event) ?? new Set<PlayerEventListener>();
    group.add(listener);
    this.listeners.set(event, group);
    return () => group.delete(listener);
  }

  emit(event: PlayerEventType, payload?: unknown): void {
    this.listeners.get(event)?.forEach((listener) => listener({ type: event, payload }));
  }
}

function makeFactory(options?: {
  failLoad?: boolean;
  failMessage?: string;
  failPlay?: { message: string; name?: string };
  gatePlay?: Promise<void>;
}) {
  const players: FakePlayer[] = [];
  const createPlayer = vi.fn((source: AudioSource) => {
    const player = new FakePlayer(
      source,
      options?.failLoad === true,
      options?.failMessage,
      options?.failPlay ?? null,
      options?.gatePlay ?? null,
    );
    players.push(player);
    return player;
  });
  return { createPlayer, players };
}

function makeApi() {
  const ok = (overrides: Partial<PlaybackState> = {}) => Promise.resolve(makeState(overrides));
  return {
    getPlayback: vi.fn(() => ok()),
    selectSong: vi.fn((_playlistId: string, _index: number) => ok()),
    openPlaylist: vi.fn((_playlistId: string) => ok()),
    next: vi.fn(() => ok()),
    previous: vi.fn(() => ok()),
    songFinished: vi.fn(() => ok()),
    skip: vi.fn((_direction: SkipDirection) => ok()),
    seek: vi.fn((_position: number) => ok()),
    report: vi.fn((_position?: number, _playing?: boolean) => ok()),
    setModes: vi.fn(() => ok()),
    spotifyPause: vi.fn((): Promise<void> => Promise.resolve()),
  };
}

function makeController(api = makeApi(), factory = makeFactory()) {
  const controller = new PlaybackController(api as unknown as ApiClient, {
    language: () => "en",
    createPlayer: factory.createPlayer,
  });
  return { controller, api, factory };
}

beforeEach(() => {
  usePlaybackStore.getState().reset();
  useToastStore.getState().reset();
  useSettingsStore.getState().reset();
  useLocalFileStore.getState().reset();
});

afterEach(() => {
  usePlaybackStore.getState().reset();
  useToastStore.getState().reset();
  useSettingsStore.getState().reset();
  useLocalFileStore.getState().reset();
});

// --- tests ------------------------------------------------------------------

describe("PlaybackController (F7 integration)", () => {
  it("starts the player when the backend says the track is playing", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, factory } = makeController();

    await controller.onTrackChange(state.song!);

    expect(factory.createPlayer).toHaveBeenCalledWith("local");
    expect(factory.players[0].playCalls).toBe(1);
    expect(factory.players[0].destroyed).toBe(false);
    await controller.onTrackChange(null);
  });

  it("leaves the player paused when the backend state is paused", async () => {
    const state = makeState({ playing: false });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, factory } = makeController();

    await controller.onTrackChange(state.song!);

    expect(factory.players[0].pauseCalls).toBeGreaterThan(0);
    expect(factory.players[0].playCalls).toBe(0);
    await controller.onTrackChange(null);
  });

  it("resumes a saved position after a reload, restarting at zero at the tail", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ playing: true, position: 42 }));
    const first = makeController();
    await first.controller.onTrackChange(makeSong("local:1"));
    expect(first.factory.players[0].loadedWith).toEqual({ source: "local:1", startTime: 42 });
    await first.controller.onTrackChange(null);

    usePlaybackStore.getState().setPlayback(
      makeState({ playing: true, position: 200, song: makeSong("local:1") }),
    );
    const second = makeController();
    await second.controller.onTrackChange(makeSong("local:1"));
    expect(second.factory.players[0].loadedWith).toEqual({ source: "local:1" });
    await second.controller.onTrackChange(null);
  });

  it("moves the live playhead when seeking inside the track", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(state.song!);
    api.seek.mockResolvedValue(makeState({ position: 42 }));

    await controller.seek(42);

    expect(api.seek).toHaveBeenCalledWith(42);
    expect(factory.players[0].seekCalls).toContain(42);
    expect(usePlaybackStore.getState().playback?.position).toBe(42);
    await controller.onTrackChange(null);
  });

  it("does not sync the old player with the answer when the song changed", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(state.song!);
    api.skip.mockResolvedValue(
      makeState({ song: makeSong("local:2"), index: 1, position: 0, playing: true }),
    );

    await controller.skip("forward");

    expect(api.skip).toHaveBeenCalledWith("forward");
    // The optimistic scrub (+5s) touched it live, but the answer's position
    // belongs to another song and must never be seeked into the old player.
    expect(factory.players[0].seekCalls).toEqual([5]);
    await controller.onTrackChange(null);
  });

  it("restarts the same song from zero when it is re-selected", async () => {
    const state = makeState({ playing: true, index: 0 });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(state.song!);
    api.selectSong.mockResolvedValue(makeState({ playing: true, position: 0, index: 0 }));

    await controller.select("pl-1", 0);

    expect(factory.players[0].seekCalls).toContain(0);
    expect(factory.createPlayer).toHaveBeenCalledTimes(1); // no reload needed
    await controller.onTrackChange(null);
  });

  it("pauses the Spotify device when a local track takes over", async () => {
    const spotify = makeSong("abc123", "spotify");
    usePlaybackStore.getState().setPlayback(makeState({ song: spotify, playing: true }));
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(spotify);
    expect(factory.players).toHaveLength(1);

    const local = makeSong("local:2");
    usePlaybackStore.getState().setPlayback(makeState({ song: local, playing: true }));
    await controller.onTrackChange(local);

    expect(api.spotifyPause).toHaveBeenCalledTimes(1);
    expect(factory.players[0].destroyed).toBe(true);
    expect(factory.players).toHaveLength(2);
    await controller.onTrackChange(null);
  });

  it("keeps the device running between two Spotify tracks", async () => {
    const first = makeSong("abc123", "spotify");
    const second = makeSong("def456", "spotify");
    usePlaybackStore.getState().setPlayback(makeState({ song: first, playing: true }));
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(first);

    usePlaybackStore.getState().setPlayback(makeState({ song: second, playing: true }));
    await controller.onTrackChange(second);

    expect(api.spotifyPause).not.toHaveBeenCalled();
    expect(factory.players[0].destroyed).toBe(true);
    await controller.onTrackChange(null);
  });

  it("still attaches the local track when pausing the device fails", async () => {
    const spotify = makeSong("abc123", "spotify");
    usePlaybackStore.getState().setPlayback(makeState({ song: spotify, playing: true }));
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(spotify);
    api.spotifyPause.mockRejectedValue(new Error("no active device"));

    const local = makeSong("local:2");
    usePlaybackStore.getState().setPlayback(makeState({ song: local, playing: true }));
    await controller.onTrackChange(local);

    expect(factory.players).toHaveLength(2);
    expect(factory.players[1].destroyed).toBe(false);
    await controller.onTrackChange(null);
  });

  it("reloads the same track when repeat=one finishes it", async () => {
    const state = makeState({ playing: true, repeat: "one" });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(state.song!);
    api.songFinished.mockResolvedValue(makeState({ playing: true, position: 0, repeat: "one" }));

    await controller.songFinished();

    expect(api.songFinished).toHaveBeenCalled();
    expect(factory.players).toHaveLength(2);
    expect(factory.players[0].destroyed).toBe(true);
    expect(factory.players[1].playCalls).toBe(1);
    await controller.onTrackChange(null);
  });

  it("stops silently when the last track finishes", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(state.song!);
    api.songFinished.mockResolvedValue(makeState({ playing: false }));

    await controller.songFinished();

    expect(factory.players).toHaveLength(1);
    expect(factory.players[0].destroyed).toBe(true);
    expect(usePlaybackStore.getState().playback?.playing).toBe(false);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("rebuilds the player when play is pressed after the queue stopped", async () => {
    const state = makeState({ playing: false });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();

    // Simulate user gesture for autoplay policy
    controller.markUserGesture();

    const result = await controller.togglePlaying();

    expect(factory.createPlayer).toHaveBeenCalledTimes(1);
    expect(factory.players[0].playCalls).toBeGreaterThan(0);
    expect(api.report).toHaveBeenCalledWith(undefined, true);
    expect(result?.playing).toBe(true);
    await controller.onTrackChange(null);
  });

  it("applies live volume and mute changes to the running player", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, factory } = makeController();
    await controller.onTrackChange(state.song!);

    useSettingsStore.getState().setVolume(0.3);
    expect(factory.players[0].volumeCalls).toContain(0.3);

    useSettingsStore.getState().setMuted(true);
    expect(factory.players[0].muted).toBe(true);
    await controller.onTrackChange(null);
  });

  it("mirrors player time updates into the store", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, factory } = makeController();
    await controller.onTrackChange(state.song!);

    factory.players[0].emit("timeupdate", { currentTime: 7 });

    expect(usePlaybackStore.getState().playback?.position).toBe(7);
    expect(usePlaybackStore.getState().playback?.playing).toBe(true);
    await controller.onTrackChange(null); // clears the pending position report
  });

  it("surfaces a failed load as a toast and keeps no player around", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller } = makeController(makeApi(), makeFactory({ failLoad: true }));

    await controller.onTrackChange(state.song!);

    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("error");
  });

  it("restores a reloaded track paused when the browser blocks autoplay (F5)", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController(
      makeApi(),
      makeFactory({
        failPlay: {
          message: "play() failed because the user didn't interact with the document first",
          name: "NotAllowedError",
        },
      }),
    );

    await controller.onTrackChange(state.song!);

    expect(factory.players[0].playCalls).toBe(1);
    expect(factory.players[0].pauseCalls).toBeGreaterThan(0);
    expect(api.report).toHaveBeenCalledWith(undefined, false);
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("info");
    expect(toasts[0].text).toContain("Click on the page"); // `autoplayBlocked`
    await controller.onTrackChange(null);
  });

  it("keeps reporting a real playback failure as an error toast", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, factory } = makeController(
      makeApi(),
      makeFactory({ failPlay: { message: "device disconnected" } }),
    );

    await controller.onTrackChange(state.song!);

    expect(factory.players[0].pauseCalls).toBe(0);
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("error");
    expect(toasts[0].text).toContain("device disconnected");
    await controller.onTrackChange(null);
  });

  it("offers to re-link a local track whose bytes are gone (F5)", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller } = makeController(
      makeApi(),
      makeFactory({
        failLoad: true,
        failMessage: `No object URL found for local track ${state.song!.id}`,
      }),
    );

    await controller.onTrackChange(state.song!);

    expect(useLocalFileStore.getState().missing).toContain("local:1");
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].text).toContain("not on this device");
    expect(useToastStore.getState().toasts[0].text).not.toContain("Error:");
  });

  it("refuses to step past the tail and says why instead of pausing", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ available_next: false, playing: true }));
    const { controller, api } = makeController();

    const result = await controller.next();

    expect(api.next).not.toHaveBeenCalled();
    expect(result).toBeNull();
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("info");
    expect(toasts[0].text).toContain("last song");
  });

  it("refuses to step before the head and says why instead of pausing", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ available_previous: false }));
    const { controller, api } = makeController();

    const result = await controller.previous();

    expect(api.previous).not.toHaveBeenCalled();
    expect(result).toBeNull();
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("info");
    expect(toasts[0].text).toContain("first song");
  });
});

describe("PlaybackController resilience", () => {
  it("drops a stale answer when a newer request already applied", async () => {
    const { controller, api } = makeController();
    usePlaybackStore.getState().setPlayback(makeState({ index: 0, position: 0 }));

    let releaseSeek!: (state: PlaybackState) => void;
    api.seek.mockImplementation(
      () =>
        new Promise<PlaybackState>((resolve) => {
          releaseSeek = resolve;
        }),
    );
    api.next.mockResolvedValue(makeState({ index: 1, position: 0 }));

    const seekInFlight = controller.seek(42); // slow answer (seq 1)
    await controller.next(); // fast answer (seq 2) lands first
    releaseSeek(makeState({ index: 0, position: 42 })); // stale now
    await seekInFlight;

    expect(usePlaybackStore.getState().playback?.index).toBe(1);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("rebuilds the backend context and retries once after a restart", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ playlist_id: "pl-1", index: 1 }));
    const { controller, api } = makeController();
    api.next
      .mockRejectedValueOnce(
        new ApiError(404, "no_active_playback", "no playlist is being played"),
      )
      .mockResolvedValue(makeState({ index: 2 }));

    const result = await controller.next();

    expect(api.selectSong).toHaveBeenCalledWith("pl-1", 1);
    expect(api.next).toHaveBeenCalledTimes(2);
    expect(result?.index).toBe(2);
    expect(usePlaybackStore.getState().playback?.index).toBe(2);
    expect(useToastStore.getState().toasts).toHaveLength(0); // silent recovery
  });

  it("drops the dead state and still reports when the playlist is gone", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ playlist_id: "pl-1", index: 0 }));
    const { controller, api } = makeController();
    api.next.mockRejectedValueOnce(
      new ApiError(404, "no_active_playback", "no playlist is being played"),
    );
    api.selectSong.mockRejectedValue(new ApiError(404, "not_found", "playlist not found"));
    api.getPlayback.mockRejectedValue(new ApiError(404, "not_found", "playlist not found"));

    const result = await controller.next();

    expect(api.selectSong).toHaveBeenCalledWith("pl-1", 0);
    expect(result).toBeNull();
    expect(usePlaybackStore.getState().playback).toBeNull();
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("error");
    expect(toasts[0].text).toContain("no playlist is being played");
  });

  it("shows the localised timeout copy when a transport call hangs", async () => {
    usePlaybackStore.getState().setPlayback(makeState());
    const { controller, api } = makeController();
    api.next.mockRejectedValue(new ApiError(0, "timeout", "request timed out"));

    const result = await controller.next();

    expect(result).toBeNull();
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].kind).toBe("error");
    expect(toasts[0].text).toContain("The server took too long to respond");
  });
});

describe("PlaybackController optimistic UI", () => {
  beforeEach(() => {
    usePlaylistStore.getState().setPlaylists([
      {
        id: "pl-1",
        name: "Queue",
        size: 3,
        current_index: 0,
        songs: [makeSong("local:1"), makeSong("local:2"), makeSong("local:3")],
      },
    ]);
  });

  afterEach(() => {
    usePlaylistStore.getState().setPlaylists([]);
  });

  /** A request that never resolves until the test releases it. */
  function hang(): { promise: Promise<PlaybackState>; release: (state: PlaybackState) => void } {
    let release!: (state: PlaybackState) => void;
    const promise = new Promise<PlaybackState>((resolve) => {
      release = resolve;
    });
    return { promise, release };
  }

  it("shows the next song before the server answers", async () => {
    usePlaybackStore.getState().setPlayback(
      makeState({ index: 0, next_index: 1, previous_index: null }),
    );
    const { controller, api } = makeController();
    const hung = hang();
    api.next.mockReturnValue(hung.promise);

    const inFlight = controller.next(); // not awaited yet

    expect(usePlaybackStore.getState().playback?.index).toBe(1);
    expect(usePlaybackStore.getState().playback?.song?.id).toBe("local:2");

    hung.release(makeState({ index: 1, position: 0 }));
    await inFlight;
    expect(usePlaybackStore.getState().playback?.index).toBe(1);
  });

  it("moves the progress bar before the seek is confirmed", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ position: 10, playing: true }));
    const { controller, api } = makeController();
    await controller.onTrackChange(makeState().song!);
    const hung = hang();
    api.seek.mockReturnValue(hung.promise);

    const inFlight = controller.seek(120);

    expect(usePlaybackStore.getState().playback?.position).toBe(120);

    hung.release(makeState({ position: 120 }));
    await inFlight;
    expect(usePlaybackStore.getState().playback?.position).toBe(120);
    await controller.onTrackChange(null);
  });

  it("backing up past 0:00 jumps to the previous song at once", async () => {
    usePlaybackStore.getState().setPlayback(
      makeState({ index: 1, position: 3, next_index: 2, previous_index: 0 }),
    );
    const { controller, api } = makeController();
    const hung = hang();
    api.skip.mockReturnValue(hung.promise);

    const inFlight = controller.skip("backward"); // 3 <= skip_seconds (5)

    expect(usePlaybackStore.getState().playback?.song?.id).toBe("local:1");
    expect(usePlaybackStore.getState().playback?.index).toBe(0);
    expect(usePlaybackStore.getState().playback?.position).toBe(0);

    hung.release(makeState({ index: 0, song: makeSong("local:1"), position: 0 }));
    await inFlight;
    expect(usePlaybackStore.getState().playback?.song?.id).toBe("local:1");
  });

  it("rolls back an optimistic pause when the report fails", async () => {
    const state = makeState({ playing: true });
    usePlaybackStore.getState().setPlayback(state);
    const { controller, api, factory } = makeController();
    await controller.onTrackChange(state.song!);
    api.report.mockRejectedValue(new Error("server down"));

    const result = await controller.togglePlaying();

    expect(result).toBeNull();
    expect(usePlaybackStore.getState().playback?.playing).toBe(true); // restored
    expect(factory.players[0].isPlaying).toBe(true); // the audio was resumed too
    expect(useToastStore.getState().toasts).toHaveLength(1);
    await controller.onTrackChange(null);
  });

  it("answers the play click before the player has started the audio", async () => {
    const state = makeState({ playing: false });
    usePlaybackStore.getState().setPlayback(state);
    let release!: () => void;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const { controller, api, factory } = makeController(makeApi(), makeFactory({ gatePlay: gate }));
    await controller.onTrackChange(state.song!); // attaches paused

    const inFlight = controller.togglePlaying();

    // The store already says "playing" while `play()` is stuck on the gate.
    expect(usePlaybackStore.getState().playback?.playing).toBe(true);

    release();
    await inFlight;
    expect(factory.players[0].playCalls).toBeGreaterThan(0);
    expect(api.report).toHaveBeenCalledWith(undefined, true);
    expect(usePlaybackStore.getState().playback?.playing).toBe(true);
    await controller.onTrackChange(null);
  });

  it("flips repeat before the modes round trip lands", async () => {
    usePlaybackStore.getState().setPlayback(makeState({ repeat: "off" }));
    const { controller, api } = makeController();
    const hung = hang();
    api.setModes.mockReturnValue(hung.promise);

    const inFlight = controller.setRepeat("all");

    expect(usePlaybackStore.getState().playback?.repeat).toBe("all");

    hung.release(makeState({ repeat: "all" }));
    await inFlight;
    expect(usePlaybackStore.getState().playback?.repeat).toBe("all");
  });
});
