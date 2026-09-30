/** Transport use cases with real audio (`F5`).

 * The backend owns the canonical position/modes (`PLAYER-011`); the local
 * audio element drives UI and reports back. `songFinished` is triggered by
 * the audio element's `ended` event.
 */

import { ApiClient, ApiError } from "./apiClient";
import { createPlayerForSource } from "../players/PlayerFactory";
import type { AudioPlayer } from "../players/AudioPlayer";
import type { PlaybackState, RepeatMode, SkipDirection, Song } from "../domain/types";
import { usePlaybackStore } from "../state/playbackStore";
import { useSettingsStore } from "../state/settingsStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface PlaybackControllerOptions {
  readonly language: () => Language;
}

export class PlaybackController {
  private readonly api: ApiClient;
  private readonly language: () => Language;
  private player: AudioPlayer | null = null;
  private unsubscribeEnded: (() => void) | null = null;
  private unsubscribeTimeUpdate: (() => void) | null = null;
  private reportTimer: number | null = null;

  constructor(api: ApiClient, options: PlaybackControllerOptions) {
    this.api = api;
    this.language = options.language;
  }

  /** Load the transport state from backend. */
  async refresh(): Promise<PlaybackState | null> {
    try {
      const state = await this.api.getPlayback();
      usePlaybackStore.getState().setPlayback(state);
      return state;
    } catch (cause) {
      if (cause instanceof ApiError && (cause.status === 404 || cause.code === "not_found")) {
        usePlaybackStore.getState().setPlayback(null);
        return null;
      }
      this.fail(cause);
      return null;
    }
  }

  /** Activate a track from a playlist. */
  async select(playlistId: string, index: number): Promise<PlaybackState | null> {
    return this.send(() => this.api.selectSong(playlistId, index));
  }

  /** Open a playlist at its first song. */
  open(playlistId: string): Promise<PlaybackState | null> {
    return this.send(() => this.api.openPlaylist(playlistId));
  }

  /** Step forward in the list. */
  next(): Promise<PlaybackState | null> {
    return this.send(() => this.api.next());
  }

  /** Step back in the list. */
  previous(): Promise<PlaybackState | null> {
    return this.send(() => this.api.previous());
  }

  /** Called when the audio element ends a track. */
  songFinished(): Promise<PlaybackState | null> {
    this.cleanupPlayer();
    return this.send(() => this.api.songFinished());
  }

  skip(direction: SkipDirection): Promise<PlaybackState | null> {
    return this.send(() => this.api.skip(direction));
  }

  seek(position: number): Promise<PlaybackState | null> {
    return this.send(() => this.api.seek(position));
  }

  /** Play or pause the real audio element, then report to backend. */
  async togglePlaying(): Promise<PlaybackState | null> {
    const current = usePlaybackStore.getState().playback;
    if (!current || !this.player) return Promise.resolve(null);

    const willPlay = !current.playing;
    if (willPlay) {
      await this.player.play();
    } else {
      this.player.pause();
    }
    return this.send(() => this.api.report(undefined, willPlay));
  }

  async setRepeat(repeat: RepeatMode): Promise<PlaybackState | null> {
    return this.send(() => this.api.setModes({ repeat }));
  }

  async toggleShuffle(): Promise<PlaybackState | null> {
    const current = usePlaybackStore.getState().playback;
    if (!current) return Promise.resolve(null);
    return this.send(() => this.api.setModes({ shuffle: !current.shuffle }));
  }

  /** Load the actual audio file for a local track. */
  async loadLocalTrack(song: Song, startTime?: number): Promise<void> {
    if (song.source !== "local" || !song.id.startsWith("local:")) {
      throw new Error("loadLocalTrack only supports local tracks");
    }
    await this.attachPlayer(createPlayerForSource("local"), song, startTime);
  }

  /** Drive the Web Playback SDK for a Spotify track (`F6`). */
  async loadSpotifyTrack(song: Song, startTime?: number): Promise<void> {
    await this.attachPlayer(createPlayerForSource("spotify", { api: this.api }), song, startTime);
  }

  /** Wire a fresh player instance to the stores and start playback. */
  private async attachPlayer(
    player: AudioPlayer,
    song: Song,
    startTime?: number,
  ): Promise<void> {
    this.cleanupPlayer();
    this.player = player;

    this.unsubscribeEnded = player.on("ended", () => {
      this.songFinished();
    });
    this.unsubscribeTimeUpdate = player.on("timeupdate", ({ payload }) => {
      const pos = (payload as { currentTime: number }).currentTime;
      usePlaybackStore.setState((prev) => {
        if (!prev.playback) return prev;
        return { ...prev, playback: { ...prev.playback, position: pos, playing: true } };
      });
      this.scheduleReport(pos);
    });

    try {
      const loadOptions = startTime !== undefined ? { startTime } : {};
      await player.load(song.id, loadOptions);
      await player.setVolume(useSettingsStore.getState().volume);
      player.setMuted(useSettingsStore.getState().muted);
    } catch (cause) {
      this.cleanupPlayer();
      throw cause;
    }
  }

  /** Called when the active track changes (e.g. next/previous/select). */
  async onTrackChange(song: Song | null): Promise<void> {
    if (!song) {
      this.cleanupPlayer();
      return;
    }
    try {
      if (song.source === "local") {
        await this.loadLocalTrack(song);
      } else {
        await this.loadSpotifyTrack(song);
      }
    } catch (cause) {
      this.cleanupPlayer();
      this.fail(cause);
    }
  }

  private scheduleReport(position: number): void {
    if (this.reportTimer !== null) return;
    this.reportTimer = window.setTimeout(() => {
      this.reportTimer = null;
      this.send(() => this.api.report(position, true));
    }, 1000); // throttle position reports
  }

  /** Clean up the current player and its listeners. */
  private cleanupPlayer(): void {
    if (this.unsubscribeEnded) {
      this.unsubscribeEnded();
      this.unsubscribeEnded = null;
    }
    if (this.unsubscribeTimeUpdate) {
      this.unsubscribeTimeUpdate();
      this.unsubscribeTimeUpdate = null;
    }
    if (this.reportTimer !== null) {
      clearTimeout(this.reportTimer);
      this.reportTimer = null;
    }
    if (this.player) {
      this.player.destroy();
      this.player = null;
    }
  }

  private async send(request: () => Promise<PlaybackState>): Promise<PlaybackState | null> {
    try {
      const state = await request();
      usePlaybackStore.getState().setPlayback(state);
      return state;
    } catch (cause) {
      this.fail(cause);
      return null;
    }
  }

  private fail(cause: unknown): void {
    const message = cause instanceof Error ? cause.message : String(cause);
    useToastStore
      .getState()
      .push("error", translate(this.language(), "toast.error", { message }));
  }

  static get errorKey(): MessageKey {
    return "toast.error";
  }
}