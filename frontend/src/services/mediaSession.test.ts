// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MediaSessionBridge } from "./mediaSession";
import type { PlaybackController } from "./PlaybackController";
import type { PlaybackState, Song } from "../domain/types";
import { usePlaybackStore } from "../state/playbackStore";

type ActionHandler = (details: MediaSessionActionDetails) => void;

interface FakeMediaSession {
  metadata: unknown;
  playbackState: MediaSessionPlaybackState;
  handlers: Map<string, ActionHandler | null>;
  setActionHandler: ReturnType<typeof vi.fn>;
  setPositionState: ReturnType<typeof vi.fn>;
}

function installMediaSession(): FakeMediaSession {
  const handlers = new Map<string, ActionHandler | null>();
  const session: FakeMediaSession = {
    metadata: null,
    playbackState: "none",
    handlers,
    setActionHandler: vi.fn((action: string, handler: ActionHandler | null) => {
      handlers.set(action, handler);
    }),
    setPositionState: vi.fn(),
  };
  Object.defineProperty(navigator, "mediaSession", { value: session, configurable: true });
  return session;
}

function makeSong(overrides: Partial<Song> = {}): Song {
  return {
    id: "local:1",
    title: "Song",
    artist: "Artist",
    source: "local",
    duration: 200,
    duration_label: "3:20",
    album: "Album",
    artwork_url: "https://example.com/cover.jpg",
    external_url: null,
    available: true,
    favorite: false,
    ...overrides,
  };
}

function makeState(overrides: Partial<PlaybackState> = {}): PlaybackState {
  return {
    playlist_id: "pl-1",
    song: makeSong(),
    index: 0,
    position: 12,
    playing: true,
    repeat: "off",
    shuffle: false,
    size: 1,
    available_next: false,
    available_previous: false,
    next_index: null,
    previous_index: null,
    skip_seconds: 5,
    ...overrides,
  };
}

function makeController() {
  return {
    play: vi.fn().mockResolvedValue(null),
    pause: vi.fn().mockResolvedValue(null),
    previous: vi.fn().mockResolvedValue(null),
    next: vi.fn().mockResolvedValue(null),
    skip: vi.fn().mockResolvedValue(null),
    seek: vi.fn().mockResolvedValue(null),
  } as unknown as PlaybackController;
}

beforeEach(() => {
  vi.stubGlobal(
    "MediaMetadata",
    class {
      constructor(readonly init: MediaMetadataInit) {}
    },
  );
});

afterEach(() => {
  usePlaybackStore.getState().reset();
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "mediaSession");
});

describe("MediaSessionBridge", () => {
  it("publishes metadata and forwards the OS handlers to the controller", () => {
    const session = installMediaSession();
    usePlaybackStore.getState().setPlayback(makeState());
    const controller = makeController();
    const bridge = new MediaSessionBridge(controller);

    bridge.start();

    expect(session.metadata).toBeInstanceOf(MediaMetadata);
    expect(session.playbackState).toBe("playing");
    expect(session.handlers.get("play")).toBeTypeOf("function");

    session.handlers.get("play")?.({ action: "play" } as MediaSessionActionDetails);
    session.handlers.get("seekto")?.({
      action: "seekto",
      seekTime: 30,
    } as MediaSessionActionDetails);

    expect(controller.play).toHaveBeenCalledTimes(1);
    expect(controller.seek).toHaveBeenCalledWith(30);
    bridge.stop();
  });

  it("mirrors play and pause into the OS playback state", () => {
    const session = installMediaSession();
    usePlaybackStore.getState().setPlayback(makeState({ playing: true }));
    const bridge = new MediaSessionBridge(makeController());
    bridge.start();

    expect(session.playbackState).toBe("playing");

    usePlaybackStore.getState().setPlayback(makeState({ playing: false }));
    expect(session.playbackState).toBe("paused");
    bridge.stop();
  });

  it("clears metadata and handlers on stop", () => {
    const session = installMediaSession();
    usePlaybackStore.getState().setPlayback(makeState());
    const bridge = new MediaSessionBridge(makeController());
    bridge.start();

    bridge.stop();

    expect(session.metadata).toBeNull();
    expect(session.playbackState).toBe("none");
    expect(session.handlers.get("play")).toBeNull();
  });

  it("is a no-op when the browser has no Media Session API", () => {
    Reflect.deleteProperty(navigator, "mediaSession");
    const bridge = new MediaSessionBridge(makeController());

    expect(() => bridge.start()).not.toThrow();
    expect(() => bridge.stop()).not.toThrow();
  });
});
