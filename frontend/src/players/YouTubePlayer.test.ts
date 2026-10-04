// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { YouTubePlayer, disposeYouTubeEngine } from "./YouTubePlayer";
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
  loadedVideos: string[] = [];
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
  loadVideoById(videoId: string, startSeconds?: number): void {
    this.loadedVideos.push(videoId);
    this.playing = false;
    if (startSeconds !== undefined) {
      this.seekedTo = startSeconds;
      this.currentTime = startSeconds;
    }
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
  emitError(code: number): void {
    this.options.events?.onError?.({ target: this, data: code });
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
  disposeYouTubeEngine();
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

  it("reuses the same inner player and loads the new video on a source switch", async () => {
    const { player } = await loaded("first");
    const firstInner = created[0];

    await player.load("second");

    // Same iframe, new video: the player is not rebuilt (`F12`).
    expect(created).toHaveLength(1);
    expect(firstInner.destroyed).toBe(false);
    expect(firstInner.loadedVideos).toContain("second");
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

  it("maps embedding-disabled errors (100/101/150) to a playable signal", async () => {
    const { player, inner } = await loaded();
    const onError = vi.fn();
    player.on("error", onError);

    inner.emitError(150);

    expect(onError).toHaveBeenCalledTimes(1);
    expect((onError.mock.calls[0][0] as { payload: { error: string } }).payload.error).toBe(
      "youtube_unplayable",
    );
  });

  it("keeps other YouTube errors as codes", async () => {
    const { player, inner } = await loaded();
    const onError = vi.fn();
    player.on("error", onError);

    inner.emitError(2);

    expect((onError.mock.calls[0][0] as { payload: { error: string } }).payload.error).toBe(
      "youtube_error_2",
    );
  });

  it("pauses and detaches but keeps the shared iframe for the next track", async () => {
    const { player, inner } = await loaded();
    inner.playing = true;

    player.destroy();

    expect(inner.playing).toBe(false); // stale audio stopped
    expect(inner.destroyed).toBe(false); // the iframe is reused (`F12`)
    expect(document.getElementById("migmusic-youtube-host")).not.toBeNull();
  });
});
