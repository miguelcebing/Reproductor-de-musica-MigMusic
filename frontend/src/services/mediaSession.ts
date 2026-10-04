/** Media Session bridge: lock-screen and notification metadata + controls (`F12`).
 *
 * The OS asks the page for what is playing and forwards play/pause/next/prev
 * presses back. This class is the only place that touches
 * `navigator.mediaSession`; it mirrors the playback store and delegates every
 * action to the existing `PlaybackController`, so no transport logic is
 * duplicated here.
 */

import type { PlaybackController } from "./PlaybackController";
import type { PlaybackState, Song } from "../domain/types";
import { usePlaybackStore } from "../state/playbackStore";

/** Media actions this app answers; anything else keeps the platform default. */
const HANDLED_ACTIONS = [
  "play",
  "pause",
  "previoustrack",
  "nexttrack",
  "seekbackward",
  "seekforward",
  "seekto",
] as const;

type HandledAction = (typeof HANDLED_ACTIONS)[number];

/** Whether the browser exposes the Media Session API at all. */
function supportsMediaSession(): boolean {
  return typeof navigator !== "undefined" && "mediaSession" in navigator;
}

/** Build the platform metadata object, or `null` where unsupported. */
function buildMetadata(song: Song): MediaMetadata | null {
  if (typeof MediaMetadata === "undefined") return null;
  const artwork: MediaImage[] = song.artwork_url ? [{ src: song.artwork_url }] : [];
  return new MediaMetadata({
    title: song.title,
    artist: song.artist,
    album: song.album ?? "",
    artwork,
  });
}

export class MediaSessionBridge {
  private unsubscribe: (() => void) | null = null;
  /** Last artwork shown, so metadata is rebuilt only when the cover changes. */
  private artworkUrl: string | null = null;

  constructor(private readonly controller: PlaybackController) {}

  /** Subscribe to the store and register the OS action handlers (idempotent). */
  start(): void {
    if (!supportsMediaSession()) return;
    this.registerHandlers();
    this.unsubscribe = usePlaybackStore.subscribe((state) => this.sync(state.playback));
    this.sync(usePlaybackStore.getState().playback);
  }

  /** Detach listeners and clear the OS metadata (no audio side effects). */
  stop(): void {
    this.unsubscribe?.();
    this.unsubscribe = null;
    if (!supportsMediaSession()) return;
    const session = navigator.mediaSession;
    for (const action of HANDLED_ACTIONS) {
      try {
        session.setActionHandler(action, null);
      } catch {
        // Some engines reject actions they do not implement; ignore them.
      }
    }
    session.metadata = null;
    session.playbackState = "none";
    this.artworkUrl = null;
  }

  private registerHandlers(): void {
    const session = navigator.mediaSession;
    const controller = this.controller;
    const handlers: Record<HandledAction, (details: MediaSessionActionDetails) => void> = {
      play: () => void controller.play(),
      pause: () => void controller.pause(),
      previoustrack: () => void controller.previous(),
      nexttrack: () => void controller.next(),
      seekbackward: () => void controller.skip("backward"),
      seekforward: () => void controller.skip("forward"),
      seekto: (details) => {
        if (typeof details.seekTime === "number") void controller.seek(details.seekTime);
      },
    };
    for (const action of HANDLED_ACTIONS) {
      try {
        session.setActionHandler(action, handlers[action]);
      } catch {
        // Unsupported action (older browser): leave the platform default.
      }
    }
  }

  /** Mirror the store into the OS: metadata, play state and scrubber. */
  private sync(playback: PlaybackState | null): void {
    if (!supportsMediaSession()) return;
    const session = navigator.mediaSession;
    const song = playback?.song ?? null;
    if (!song) {
      session.metadata = null;
      session.playbackState = "none";
      this.artworkUrl = null;
      return;
    }
    if (song.artwork_url !== this.artworkUrl) {
      this.artworkUrl = song.artwork_url;
      session.metadata = buildMetadata(song);
    }
    session.playbackState = playback?.playing ? "playing" : "paused";
    this.syncPosition(playback);
  }

  private syncPosition(playback: PlaybackState | null): void {
    const session = navigator.mediaSession;
    if (typeof session.setPositionState !== "function") return;
    const duration = playback?.song?.duration ?? 0;
    if (!(duration > 0)) return;
    const position = Math.min(Math.max(playback?.position ?? 0, 0), duration);
    try {
      session.setPositionState({ duration, playbackRate: 1, position });
    } catch {
      // Invalid state (e.g. NaN duration from a broken source): skip the tick.
    }
  }
}
