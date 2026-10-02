import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { READY_TIMEOUT_MS, WebPlaybackSession } from "./spotifySdk";

/** Stand-in for the raw SDK player: records listeners, connects, disconnects. */
class FakeSdkPlayer {
  static instances: FakeSdkPlayer[] = [];
  static readyAfterMs: number | null = 0;
  static emitOnConnect: { event: string; message: string } | null = null;
  static connectResult = true;

  readonly listeners = new Map<string, ((data: never) => void)[]>();
  connectCalls = 0;
  disconnected = 0;

  constructor() {
    FakeSdkPlayer.instances.push(this);
  }

  addListener(event: string, cb: (data: never) => void): boolean {
    const list = this.listeners.get(event) ?? [];
    list.push(cb);
    this.listeners.set(event, list);
    return true;
  }

  removeListener(): boolean {
    return true;
  }

  connect(): Promise<boolean> {
    this.connectCalls += 1;
    const emit = FakeSdkPlayer.emitOnConnect;
    if (emit) {
      this.emit(emit.event, { message: emit.message });
    } else if (FakeSdkPlayer.readyAfterMs !== null) {
      setTimeout(() => this.emit("ready", { device_id: "device-abc" }), FakeSdkPlayer.readyAfterMs);
    }
    return Promise.resolve(FakeSdkPlayer.connectResult);
  }

  disconnect(): void {
    this.disconnected += 1;
  }

  getCurrentState(): Promise<null> {
    return Promise.resolve(null);
  }

  pause(): Promise<void> {
    return Promise.resolve();
  }

  resume(): Promise<void> {
    return Promise.resolve();
  }

  seek(): Promise<void> {
    return Promise.resolve();
  }

  setVolume(): Promise<void> {
    return Promise.resolve();
  }

  emit(event: string, data: unknown): void {
    this.listeners.get(event)?.forEach((cb) => cb(data as never));
  }
}

function stubWindow(): void {
  vi.stubGlobal("window", { Spotify: { Player: FakeSdkPlayer } });
}

/** Let the connect chain reach `await ready` (it uses no timers of its own). */
async function untilConnectCalled(): Promise<FakeSdkPlayer> {
  for (let i = 0; i < 50; i += 1) {
    const player = FakeSdkPlayer.instances.at(-1);
    if (player && player.connectCalls > 0) {
      await Promise.resolve(); // let the code after `await player.connect()` run
      await Promise.resolve();
      return player;
    }
    await Promise.resolve();
  }
  throw new Error("the SDK player never connected");
}

function makeSession(): WebPlaybackSession {
  return new WebPlaybackSession(() => Promise.resolve("token"));
}

beforeEach(() => {
  FakeSdkPlayer.instances = [];
  FakeSdkPlayer.readyAfterMs = 0;
  FakeSdkPlayer.emitOnConnect = null;
  FakeSdkPlayer.connectResult = true;
  stubWindow();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("WebPlaybackSession.ensureConnected", () => {
  it("adopts the device id reported by the ready event", async () => {
    const session = makeSession();

    await session.ensureConnected();

    expect(session.deviceId).toBe("device-abc");
    expect(FakeSdkPlayer.instances).toHaveLength(1);
    expect(FakeSdkPlayer.instances[0].disconnected).toBe(0);
  });

  it("keeps one shared player for later tracks", async () => {
    const session = makeSession();
    await session.ensureConnected();

    await session.ensureConnected();

    expect(FakeSdkPlayer.instances).toHaveLength(1);
  });

  it("waits for a slow ready event instead of giving up after two seconds", async () => {
    vi.useFakeTimers();
    FakeSdkPlayer.readyAfterMs = 3_000;
    const session = makeSession();

    const pending = session.ensureConnected();
    await untilConnectCalled();
    expect(session.deviceId).toBe(""); // still waiting, not failed

    await vi.advanceTimersByTimeAsync(3_000);
    await pending;

    expect(session.deviceId).toBe("device-abc");
  });

  it("fails cleanly when the SDK never reports a device id", async () => {
    vi.useFakeTimers();
    FakeSdkPlayer.readyAfterMs = null;
    const session = makeSession();

    const pending = session.ensureConnected();
    const failure = expect(pending).rejects.toThrow(/did not report a device id/);
    await untilConnectCalled();
    await vi.advanceTimersByTimeAsync(READY_TIMEOUT_MS);
    await failure;

    expect(FakeSdkPlayer.instances[0].disconnected).toBe(1); // no half-open player lingers
    expect(session.deviceId).toBe("");

    // The next attempt starts a fresh player instead of reusing the dead one.
    FakeSdkPlayer.readyAfterMs = 0;
    const retry = session.ensureConnected();
    await untilConnectCalled();
    await vi.advanceTimersByTimeAsync(0);
    await retry;

    expect(session.deviceId).toBe("device-abc");
    expect(FakeSdkPlayer.instances).toHaveLength(2);
    expect(FakeSdkPlayer.instances[0].disconnected).toBe(1);
    expect(FakeSdkPlayer.instances[1].disconnected).toBe(0);
  });

  it("surfaces an SDK initialization error instead of waiting for the timeout", async () => {
    FakeSdkPlayer.emitOnConnect = {
      event: "initialization_error",
      message: "SDK failed to initialize",
    };
    const session = makeSession();

    await expect(session.ensureConnected()).rejects.toThrow("SDK failed to initialize");

    expect(FakeSdkPlayer.instances[0].disconnected).toBe(1);
    expect(session.deviceId).toBe("");
  });

  it("fails when the SDK refuses to connect and retries cleanly afterwards", async () => {
    FakeSdkPlayer.connectResult = false;
    const session = makeSession();

    await expect(session.ensureConnected()).rejects.toThrow(/could not connect/);
    expect(FakeSdkPlayer.instances[0].disconnected).toBe(1);
    expect(session.deviceId).toBe("");

    FakeSdkPlayer.connectResult = true;
    await session.ensureConnected();
    expect(session.deviceId).toBe("device-abc");
    expect(FakeSdkPlayer.instances).toHaveLength(2);
  });
});
