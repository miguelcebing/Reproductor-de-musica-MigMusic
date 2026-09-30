import { afterEach, describe, expect, it, vi } from "vitest";

import { SpotifyPlayer, type SpotifyPlaybackControl } from "./SpotifyPlayer";
import type { SpotifySdkSession, SpotifySdkState } from "./spotifySdk";

function playingState(uri: string, overrides: Partial<SpotifySdkState> = {}): SpotifySdkState {
  return { uri, paused: false, position: 0, duration: 200, ...overrides };
}

class FakeSession implements SpotifySdkSession {
  readonly deviceId = "device-1";
  connects = 0;
  state: SpotifySdkState | null = null;
  resumed = 0;
  pauseCalls = 0;
  seekTo: number | null = null;
  volume: number | null = null;
  private readonly stateListeners = new Set<(state: SpotifySdkState | null) => void>();
  private readonly errorListeners = new Set<(message: string) => void>();

  async ensureConnected(): Promise<void> {
    this.connects += 1;
  }

  disconnect(): void {
    // Not under test here.
  }

  resume(): Promise<void> {
    this.resumed += 1;
    this.push(this.state ? { ...this.state, paused: false } : null);
    return Promise.resolve();
  }

  pause(): Promise<void> {
    this.pauseCalls += 1;
    this.push(this.state ? { ...this.state, paused: true } : null);
    return Promise.resolve();
  }

  async seek(seconds: number): Promise<void> {
    this.seekTo = seconds;
    if (this.state) this.push({ ...this.state, position: seconds });
  }

  async setVolume(volumeLevel: number): Promise<void> {
    this.volume = volumeLevel;
  }

  async getState(): Promise<SpotifySdkState | null> {
    return this.state;
  }

  onStateChanged(listener: (state: SpotifySdkState | null) => void): () => void {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }

  onError(listener: (message: string) => void): () => void {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  push(state: SpotifySdkState | null): void {
    this.state = state;
    this.stateListeners.forEach((listener) => listener(state));
  }

  raise(message: string): void {
    this.errorListeners.forEach((listener) => listener(message));
  }
}

function makePlayer(options?: { autoStart?: boolean }) {
  const session = new FakeSession();
  const playCalls: { uris: string[]; deviceId: string; positionMs: number | undefined }[] = [];
  const control: SpotifyPlaybackControl = {
    play: (uris, deviceId, positionMs) => {
      playCalls.push({ uris: [...uris], deviceId, positionMs });
      if (options?.autoStart !== false) {
        session.push(playingState(uris[0] ?? "", { position: (positionMs ?? 0) / 1000 }));
      }
      return Promise.resolve();
    },
  };
  const player = new SpotifyPlayer({ control, session });
  return { player, session, playCalls };
}

afterEach(() => {
  vi.useRealTimers();
});

describe("SpotifyPlayer", () => {
  it("normalises a raw track id and queues it on the SDK device", async () => {
    const { player, session, playCalls } = makePlayer();
    await player.load("4uLU6hMCjMI75M1A2tKUQC", { startTime: 30 });

    expect(session.connects).toBe(1);
    expect(playCalls[0]).toEqual({
      uris: ["spotify:track:4uLU6hMCjMI75M1A2tKUQC"],
      deviceId: "device-1",
      positionMs: 30_000,
    });
    expect(player.source).toBe("spotify:track:4uLU6hMCjMI75M1A2tKUQC");
    expect(player.isPlaying).toBe(true);
    expect(player.duration).toBe(200);
    player.destroy();
  });

  it("emits timeupdate while the SDK reports the track", async () => {
    const { player, session } = makePlayer();
    const seen: number[] = [];
    player.on("timeupdate", ({ payload }) => seen.push((payload as { currentTime: number }).currentTime));
    await player.load("spotify:track:a");

    session.push(playingState("spotify:track:a", { position: 42 }));
    expect(seen).toContain(42);
    player.destroy();
  });

  it("emits ended when playback stops", async () => {
    const { player, session } = makePlayer();
    let ended = 0;
    player.on("ended", () => {
      ended += 1;
    });
    await player.load("spotify:track:a");

    session.push(null);
    expect(ended).toBe(1);
    expect(player.isPlaying).toBe(false);
    player.destroy();
  });

  it("emits pause and play across a pause/resume cycle", async () => {
    const { player, session } = makePlayer();
    const events: string[] = [];
    player.on("pause", () => events.push("pause"));
    player.on("play", () => events.push("play"));
    await player.load("spotify:track:a");

    player.pause();
    expect(session.pauseCalls).toBe(1);
    await player.play();
    expect(session.resumed).toBe(1);
    expect(events).toEqual(["pause", "play"]);
    player.destroy();
  });

  it("keeps seeks inside the track duration", async () => {
    const { player, session } = makePlayer();
    await player.load("spotify:track:a");

    await player.seek(999);
    expect(session.seekTo).toBe(200);
    expect(player.currentTime).toBe(200);

    await player.seek(-5);
    expect(session.seekTo).toBe(0);
    player.destroy();
  });

  it("maps volume and mute onto the SDK volume", async () => {
    const { player, session } = makePlayer();
    await player.load("spotify:track:a");

    player.setVolume(0.5);
    await Promise.resolve();
    expect(session.volume).toBe(0.5);

    player.setMuted(true);
    await Promise.resolve();
    expect(session.volume).toBe(0);

    player.setMuted(false);
    await Promise.resolve();
    expect(session.volume).toBe(0.5);
    expect(player.volume).toBe(0.5);
    player.destroy();
  });

  it("forwards SDK errors as player error events", async () => {
    const { player, session } = makePlayer();
    const messages: unknown[] = [];
    player.on("error", ({ payload }) => messages.push((payload as { message?: string }).message));
    await player.load("spotify:track:a");

    session.raise("Premium account required");
    expect(messages).toContain("Premium account required");
    player.destroy();
  });

  it("stops emitting once destroyed", async () => {
    const { player, session } = makePlayer();
    await player.load("spotify:track:a");
    let ended = 0;
    player.on("ended", () => {
      ended += 1;
    });

    player.destroy();
    session.push(null);
    expect(ended).toBe(0);
  });

  it("gives up when the SDK never reports the track", async () => {
    vi.useFakeTimers({
      toFake: ["setTimeout", "setInterval", "clearTimeout", "clearInterval", "Date"],
    });
    const session = new FakeSession();
    const control: SpotifyPlaybackControl = { play: () => Promise.resolve() };
    const player = new SpotifyPlayer({ control, session });

    const pending = player.load("spotify:track:x");
    const assertion = expect(pending).rejects.toThrow(/did not start/i);
    await vi.advanceTimersByTimeAsync(6_000);
    await assertion;
  });
});
