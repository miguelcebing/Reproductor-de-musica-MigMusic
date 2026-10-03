// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { YouTubePlayer } from "./YouTubePlayer";
import type {
  YouTubePlayerEvent,
  YouTubePlayerInstance,
  YouTubePlayerOptions,
} from "./youtubeIframe";

/** Records calls and lets the test drive the inner player's callbacks. */
class FakeInnerPlayer implements YouTubePlayerInstance {
  volume = 100;
  muted = false;
  playing = false;
  currentTime = 0;
  duration = 200;
  state = 1;
  destroyed = false;
  seekedTo: number | null = null;
  options: YouTubePlayerOptions;
  private readonly mount: HTMLElement;

  constructor(mount: HTMLElement | string, options: YouTubePlayerOptions) {
    this.mount = typeof mount === "string" ? document.getElementById(mount)! : mount;
    this.options = options;
  }

  playVideo(): void {
    this.playing = true;
  }
  pauseVideo(): void {
    this.playing = false;
  }
  stopVideo(): void {
    this.playing = false;
  }
  seekTo(seconds: number): void {
    this.seekedTo = seconds;
    this.currentTime = seconds;
  }
  setVolume(volume: number): void {
    this.volume = volume;
  }
  mute(): void {
    this.muted = true;
  }
  unMute(): void {
    this.muted = false;
  }
  getCurrentTime(): number {
    return this.currentTime;
  }
  getDuration(): number {
    return this.duration;
  }
  getPlayerState(): number {
    return this.state;
  }
  destroy(): void {
    this.destroyed = true;
    this.mount.remove();
  }

  ready(): void {
    const event = { target: this } as YouTubePlayerEvent;
    this.options.events?.onReady?.(event);
  }
  emitState(state: number): void {
    this.state = state;
    this.options.events?.onStateChange?.({ target: this, data: state });
  }
}

const created: FakeInnerPlayer[] = [];

function installFakeApi(): void {
  const PlayerState = { UNSTARTED: -1, ENDED: 0, PLAYING: 1, PAUSED: 2, BUFFERING: 3, CUED: 5 };
  (window as unknown as { YT: unknown }).YT = {
    PlayerState,
    Player: function Player(this: unknown, mount: HTMLElement | string, options: YouTubePlayerOptions) {
      const player = new FakeInnerPlayer(mount, options);
      created.push(player);
      return player;
    },
  };
}

beforeEach(() => {
  created.length = 0;
  document.body.innerHTML = "";
  installFakeApi();
});

afterEach(() => {
  vi.restoreAllMocks();
});

async function loaded(source = "vid1"): Promise<{ player: YouTubePlayer; inner: FakeInnerPlayer }> {
  const player = new YouTubePlayer();
  const loadPromise = player.load(source);
  // The fake API resolves on a microtask; let it settle, then fire onReady.
  await Promise.resolve();
  await Promise.resolve();
  const inner = created[created.length - 1];
  inner.ready();
  await loadPromise;
  return { player, inner };
}

describe("YouTubePlayer", () => {
  it("loads the requested videoId and reports the source", async () => {
    const { player, inner } = await loaded("abc123");

    expect(player.source).toBe("abc123");
    expect(inner.duration).toBe(200);
  });

  it("plays and pauses through the inner player", async () => {
    const { player, inner } = await loaded();

    await player.play();
    expect(inner.playing).toBe(true);
    expect(player.isPlaying).toBe(true);

    player.pause();
    expect(inner.playing).toBe(false);
    expect(player.isPlaying).toBe(false);
  });

  it("starts at the resumed position when given startTime", async () => {
    const player = new YouTubePlayer();
    const loadPromise = player.load("vid1", { startTime: 42 });
    await Promise.resolve();
    await Promise.resolve();
    const inner = created[created.length - 1];
    inner.ready();
    await loadPromise;

    expect(inner.seekedTo).toBe(42);
  });

  it("destroys the previous inner player on a source switch", async () => {
    const { player } = await loaded("first");
    const firstInner = created[0];

    const secondLoad = player.load("second");
    await Promise.resolve();
    await Promise.resolve();
    const secondInner = created[created.length - 1];
    secondInner.ready();
    await secondLoad;

    // The old inner player was stopped and destroyed: no stale audio remains.
    expect(firstInner.destroyed).toBe(true);
    expect(player.source).toBe("second");
  });

  it("maps volume and mute to the inner player", async () => {
    const { player, inner } = await loaded();

    player.setVolume(0.5);
    expect(inner.volume).toBe(50);

    player.setMuted(true);
    expect(inner.muted).toBe(true);
    player.setMuted(false);
    expect(inner.muted).toBe(false);
  });

  it("emits ended only once per track", async () => {
    const { player, inner } = await loaded();
    const onEnded = vi.fn();
    player.on("ended", onEnded);

    inner.emitState(0); // ENDED
    inner.emitState(0);

    expect(onEnded).toHaveBeenCalledTimes(1);
  });

  it("emits timeupdate while the ticker runs", async () => {
    vi.useFakeTimers();
    try {
      const player = new YouTubePlayer();
      const loadPromise = player.load("vid1");
      await Promise.resolve();
      await Promise.resolve();
      const inner = created[created.length - 1];
      inner.ready();
      await loadPromise;

      const onUpdate = vi.fn();
      player.on("timeupdate", onUpdate);
      inner.currentTime = 12;
      vi.advanceTimersByTime(1000);

      expect(onUpdate).toHaveBeenCalled();
    } finally {
      vi.useRealTimers();
    }
  });

  it("destroys cleanly and removes the host container", async () => {
    const { player, inner } = await loaded();

    player.destroy();

    expect(inner.destroyed).toBe(true);
    expect(document.getElementById("migmusic-youtube-host")).toBeNull();
  });
});
