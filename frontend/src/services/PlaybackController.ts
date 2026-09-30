/** Transport use cases with real audio (`F5`) and cross-source switching (`F7`).

 * The backend owns the canonical position/modes (`PLAYER-011`); the players
 * mirror it. Every store update that keeps the same song is pushed back into
 * the live player, so seek/skip are audible (not just visual), and releasing a
 * Spotify player pauses the SDK device before a local track takes over so the
 * two sources never play at once (`RF-12`).
 */

import { ApiClient, ApiError } from "./apiClient";
import { createPlayerForSource, type PlayerFactoryOptions } from "../players/PlayerFactory";
import type { AudioPlayer } from "../players/AudioPlayer";
import type { AudioSource, PlaybackState, RepeatMode, SkipDirection, Song } from "../domain/types";
import { usePlaybackStore } from "../state/playbackStore";
import { useSettingsStore } from "../state/settingsStore";
import { useToastStore } from "../state/toastStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

export interface PlaybackControllerOptions {
  readonly language: () => Language;
  /** Injectable factory (tests); defaults to the source-aware `PlayerFactory`. */
  readonly createPlayer?: (source: AudioSource, options?: PlayerFactoryOptions) => AudioPlayer;
}

/** Which song the backend pointed at before a request was sent. */
interface SongIdentity {
  readonly id: string | null;
  readonly index: number | null;
}

export class PlaybackController {
  private readonly api: ApiClient;
  private readonly language: () => Language;
  private readonly createPlayer: (
    source: AudioSource,
    options?: PlayerFactoryOptions,
  ) => AudioPlayer;
  private player: AudioPlayer | null = null;
  private activeSource: AudioSource | null = null;
  private attachSeq = 0;
  private unsubscribeEnded: (() => void) | null = null;
  private unsubscribeTimeUpdate: (() => void) | null = null;
  private reportTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(api: ApiClient, options: PlaybackControllerOptions) {
    this.api = api;
    this.language = options.language;
    this.createPlayer = options.createPlayer ?? createPlayerForSource;

    // Volume/mute must reach the live player immediately, not on the next track.
    useSettingsStore.subscribe((state, previous) => {
      if (state.volume !== previous.volume || state.muted !== previous.muted) {
        this.player?.setVolume(state.volume);
        this.player?.setMuted(state.muted);
      }
    });
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
    return this.commit(() => this.api.selectSong(playlistId, index));
  }

  /** Open a playlist at its first song. */
  open(playlistId: string): Promise<PlaybackState | null> {
    return this.commit(() => this.api.openPlaylist(playlistId));
  }

  /** Step forward in the list. */
  next(): Promise<PlaybackState | null> {
    return this.commit(() => this.api.next());
  }

  /** Step back in the list. */
  previous(): Promise<PlaybackState | null> {
    return this.commit(() => this.api.previous());
  }

  /** Called when the player reports the track ended. */
  async songFinished(): Promise<PlaybackState | null> {
    // Detach first so a stale listener cannot report twice; `activeSource`
    // survives so the next attach still knows a Spotify device may be live.
    this.detachPlayer();
    return this.commit(() => this.api.songFinished());
  }

  skip(direction: SkipDirection): Promise<PlaybackState | null> {
    return this.commit(() => this.api.skip(direction));
  }

  seek(position: number): Promise<PlaybackState | null> {
    return this.commit(() => this.api.seek(position));
  }

  /** Play or pause the real audio, then report to backend. */
  async togglePlaying(): Promise<PlaybackState | null> {
    const current = usePlaybackStore.getState().playback;
    if (!current?.song) return null;

    const willPlay = !current.playing;
    if (willPlay && !this.player) {
      // The track ended at the tail (or the page reloaded): rebuild the player.
      await this.onTrackChange(current.song);
      if (!this.player) return null; // load failed; the toast already says why
    }

    if (willPlay) {
      try {
        await this.player?.play();
      } catch (cause) {
        this.fail(cause);
        return null;
      }
    } else {
      this.player?.pause();
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
  async loadLocalTrack(song: Song): Promise<void> {
    if (song.source !== "local" || !song.id.startsWith("local:")) {
      throw new Error("loadLocalTrack only supports local tracks");
    }
    await this.attachPlayer(this.createPlayer("local"), song);
  }

  /** Drive the Web Playback SDK for a Spotify track (`F6`). */
  async loadSpotifyTrack(song: Song): Promise<void> {
    await this.attachPlayer(this.createPlayer("spotify", { api: this.api }), song);
  }

  /** Called when the active track changes (next/previous/select/finish). */
  async onTrackChange(song: Song | null): Promise<void> {
    if (!song) {
      await this.releasePlayer(null);
      return;
    }
    try {
      if (song.source === "local") {
        await this.loadLocalTrack(song);
      } else {
        await this.loadSpotifyTrack(song);
      }
    } catch (cause) {
      this.detachPlayer();
      this.activeSource = null;
      this.fail(cause);
    }
  }

  // ------------------------------------------------------------ internals

  /** Send a transport request and mirror the answer into the live player. */
  private async commit(request: () => Promise<PlaybackState>): Promise<PlaybackState | null> {
    const before = this.identity();
    const state = await this.send(request);
    if (state) await this.syncAfterState(state, before);
    return state;
  }

  private identity(): SongIdentity {
    const playback = usePlaybackStore.getState().playback;
    return { id: playback?.song?.id ?? null, index: playback?.index ?? null };
  }

  /**
   * Apply a backend answer to the player: same song → move the playhead (and
   * match play/pause); different song → skip, the App effect reloads instead.
   */
  private async syncAfterState(state: PlaybackState, before: SongIdentity): Promise<void> {
    const sameSong =
      (state.song?.id ?? null) === before.id && (state.index ?? null) === before.index;
    if (!sameSong) return;

    if (!this.player) {
      // repeat=one / tail-restart: no reload will come from the effect.
      if (state.playing && state.song) await this.onTrackChange(state.song);
      return;
    }

    try {
      await this.player.seek(state.position);
      if (state.playing) await this.player.play();
      else this.player.pause();
    } catch (cause) {
      this.fail(cause);
    }
  }

  /** Wire a fresh player to the stores and start it at the backend position. */
  private async attachPlayer(player: AudioPlayer, song: Song): Promise<void> {
    const seq = ++this.attachSeq;
    await this.releasePlayer(song.source);
    if (seq !== this.attachSeq) {
      player.destroy(); // superseded by a newer attach while we awaited
      return;
    }

    this.player = player;
    this.activeSource = song.source;

    this.unsubscribeEnded = player.on("ended", () => {
      void this.songFinished();
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
      const startTime = this.resumePosition();
      await player.load(song.id, startTime > 0 ? { startTime } : {});
      if (seq !== this.attachSeq) return;
      player.setVolume(useSettingsStore.getState().volume);
      player.setMuted(useSettingsStore.getState().muted);

      const shouldPlay = usePlaybackStore.getState().playback?.playing ?? false;
      if (shouldPlay) {
        try {
          await player.play();
        } catch (cause) {
          if (seq !== this.attachSeq) throw cause;
          // Autoplay blocked (no user gesture): fall back to paused so the UI
          // matches reality instead of showing a silent "playing" track.
          this.fail(cause);
          await this.send(() => this.api.report(undefined, false));
        }
      } else {
        player.pause(); // SpotifyPlayer.load starts the device; local is a no-op
      }
    } catch (cause) {
      if (seq !== this.attachSeq) return; // a newer attach owns the cleanup
      throw cause;
    }
  }

  /** Where a (re)load should start: the backend position, unless it is the end. */
  private resumePosition(): number {
    const playback = usePlaybackStore.getState().playback;
    if (!playback) return 0;
    const duration = playback.song?.duration ?? 0;
    const position = Math.max(0, playback.position);
    return duration > 0 && position >= duration - 0.5 ? 0 : position;
  }

  /**
   * Destroy the current player and, when it was the Spotify source and the
   * next track is not, pause the SDK device so audio never overlaps (`RF-12`).
   */
  private async releasePlayer(next: AudioSource | null): Promise<void> {
    const wasSpotify = this.activeSource === "spotify";
    this.detachPlayer();
    this.activeSource = null;
    if (wasSpotify && next !== "spotify") {
      try {
        await this.api.spotifyPause();
      } catch {
        // No active device (the track already stopped): nothing left to pause.
      }
    }
  }

  /** Stop listening to the player; `activeSource` is decided by the caller. */
  private detachPlayer(): void {
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

  private scheduleReport(position: number): void {
    if (this.reportTimer !== null) return;
    this.reportTimer = setTimeout(() => {
      this.reportTimer = null;
      // Read `playing` at fire time: the track may have paused meanwhile.
      const playing = usePlaybackStore.getState().playback?.playing ?? true;
      this.send(() => this.api.report(position, playing));
    }, 1000); // throttle position reports
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
