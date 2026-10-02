/** Transport use cases with real audio (`F5`) and cross-source switching (`F7`).

 * The backend owns the canonical position/modes (`PLAYER-011`); the players
 * mirror it. Every store update that keeps the same song is pushed back into
 * the live player, so seek/skip are audible (not just visual), and releasing a
 * Spotify player pauses the SDK device before a local track takes over so the
 * two sources never play at once (`RF-12`).
 */

import { ApiClient, ApiError, failureMessage } from "./apiClient";
import { createPlayerForSource, type PlayerFactoryOptions } from "../players/PlayerFactory";
import type { AudioPlayer } from "../players/AudioPlayer";
import type { AudioSource, PlaybackState, RepeatMode, SkipDirection, Song } from "../domain/types";
import { usePlaybackStore } from "../state/playbackStore";
import { usePlaylistStore } from "../state/playlistStore";
import { useSettingsStore } from "../state/settingsStore";
import { useToastStore } from "../state/toastStore";
import { useLocalFileStore } from "../state/localFileStore";
import { translate, type Language, type MessageKey } from "../i18n/messages";

/** Thrown by `LocalAudioPlayer` when IndexedDB has no bytes for the track. */
export function isMissingLocalFile(cause: unknown): boolean {
  return cause instanceof Error && cause.message.startsWith("No object URL found");
}

/** Browser autoplay rejection: a reload resumed a track with no gesture yet. */
export function isAutoplayBlocked(cause: unknown): boolean {
  const name = (cause as { name?: string } | null)?.name;
  const message = cause instanceof Error ? cause.message : "";
  return name === "NotAllowedError" || message.includes("user didn't interact");
}

/** The backend lost its playback context (restart); the client can rebuild it. */
function isNoActivePlayback(cause: unknown): boolean {
  return cause instanceof ApiError && cause.code === "no_active_playback";
}

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
  private unsubscribeError: (() => void) | null = null;
  private reportTimer: ReturnType<typeof setTimeout> | null = null;
  private userGesture = false;
  /** Newest request started; responses older than `lastAppliedSeq` are stale. */
  private requestSeq = 0;
  private lastAppliedSeq = 0;

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

    // Autoplay policy: the browser only lets audio start after a real user
    // gesture. Listening in the *capture* phase means we record it before
    // React's delegated handlers run, so the very first click already counts.
    if (typeof window !== "undefined") {
      const setGesture = () => this.markUserGesture();
      const capture: AddEventListenerOptions = { once: true, passive: true, capture: true };
      window.addEventListener("click", setGesture, capture);
      window.addEventListener("touchstart", setGesture, capture);
      window.addEventListener("keydown", setGesture, capture);
    }
  }

  /** Record that the user interacted with the page (autoplay policy). */
  markUserGesture(): void {
    this.userGesture = true;
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
    this.markUserGesture();
    return this.commit(() => this.api.selectSong(playlistId, index));
  }

  /** Open a playlist at its first song. */
  open(playlistId: string): Promise<PlaybackState | null> {
    this.markUserGesture();
    return this.commit(() => this.api.openPlaylist(playlistId));
  }

  /** Step forward in the list. */
  next(): Promise<PlaybackState | null> {
    this.markUserGesture();
    if (this.atEdge("available_next", "player.atEnd")) return Promise.resolve(null);
    return this.commit(() => this.api.next(), this.targetPatch("next_index"));
  }

  /** Step back in the list. */
  previous(): Promise<PlaybackState | null> {
    this.markUserGesture();
    if (this.atEdge("available_previous", "player.atStart")) return Promise.resolve(null);
    return this.commit(() => this.api.previous(), this.targetPatch("previous_index"));
  }

  /**
   * Manual skips stop at the edges (`PLAYLIST-009 = A`): the backend would
   * only pause the music there, so answer with a toast and touch nothing.
   */
  private atEdge(edge: "available_next" | "available_previous", key: MessageKey): boolean {
    const playback = usePlaybackStore.getState().playback;
    if (!playback || playback[edge]) return false;
    this.toast("info", key);
    return true;
  }

  /** Called when the player reports the track ended. */
  async songFinished(): Promise<PlaybackState | null> {
    // Detach first so a stale listener cannot report twice; `activeSource`
    // survives so the next attach still knows a Spotify device may be live.
    this.detachPlayer();
    return this.commit(() => this.api.songFinished());
  }

  /** Move ±`skip_seconds`; backing up near 0 crosses to the previous song. */
  skip(direction: SkipDirection): Promise<PlaybackState | null> {
    this.markUserGesture();
    const current = usePlaybackStore.getState().playback;
    if (!current?.song) return this.commit(() => this.api.skip(direction));

    if (direction === "backward" && current.position <= current.skip_seconds) {
      // Backing up past 0:00 jumps to the previous song (or rewinds at the head).
      return this.commit(
        () => this.api.skip(direction),
        this.targetPatch("previous_index") ?? { position: 0 },
      );
    }

    const delta = current.skip_seconds * (direction === "forward" ? 1 : -1);
    const duration = current.song.duration;
    const position =
      duration > 0
        ? Math.min(Math.max(current.position + delta, 0), duration)
        : Math.max(current.position + delta, 0);
    void this.player?.seek(position); // audible immediately, the answer confirms
    return this.commit(() => this.api.skip(direction), { position });
  }

  seek(position: number): Promise<PlaybackState | null> {
    this.markUserGesture();
    const current = usePlaybackStore.getState().playback;
    void this.player?.seek(position); // audible immediately, the answer just confirms
    return this.commit(
      () => this.api.seek(position),
      current ? { position } : undefined,
    );
  }

  /** Flip the transport on the click itself; the answer (and player) confirm. */
  async togglePlaying(): Promise<PlaybackState | null> {
    // This method is only reachable from a click/keypress, so it *is the
    // gesture the autoplay policy waits for (the first press must not no-op).
    this.markUserGesture();
    const current = usePlaybackStore.getState().playback;
    if (!current?.song) return null;

    const willPlay = !current.playing;
    // The button answers the click immediately; the report below confirms it
    // and rolls both the store and the player back if something refuses.
    const snapshot = current;
    usePlaybackStore.getState().setPlayback({ ...snapshot, playing: willPlay });

    let player = this.player;
    if (willPlay) {
      if (!player) {
        // The track ended at the tail (or the page reloaded): rebuild the player.
        await this.onTrackChange(current.song);
        player = this.player;
        if (!player) {
          usePlaybackStore.getState().setPlayback(snapshot); // load failed; the toast already says why
          return null;
        }
      }
      try {
        await player.play();
      } catch (cause) {
        usePlaybackStore.getState().setPlayback(snapshot);
        this.fail(cause);
        return null;
      }
    } else {
      player?.pause();
    }
    return this.send(
      () => this.api.report(undefined, willPlay),
      { playing: willPlay },
      snapshot,
    );
  }

  async setRepeat(repeat: RepeatMode): Promise<PlaybackState | null> {
    return this.send(() => this.api.setModes({ repeat }), { repeat });
  }

  async toggleShuffle(): Promise<PlaybackState | null> {
    const current = usePlaybackStore.getState().playback;
    if (!current) return Promise.resolve(null);
    return this.send(
      () => this.api.setModes({ shuffle: !current.shuffle }),
      { shuffle: !current.shuffle },
    );
  }

  /** Stop playback and clear the playback state (e.g., when playlist is deleted). */
  async stop(): Promise<void> {
    this.detachPlayer();
    usePlaybackStore.getState().setPlayback(null);
    try {
      await this.api.report(undefined, false);
    } catch {
      // Ignore reporting errors when stopping
    }
  }

  /** Load the actual audio file for a local track. */
  private async loadLocalTrack(song: Song): Promise<void> {
    if (song.source !== "local" || !song.id.startsWith("local:")) {
      throw new Error("loadLocalTrack only supports local tracks");
    }
    await this.attachPlayer(this.createPlayer("local"), song);
  }

  /** Drive the Web Playback SDK for a Spotify track (`F6`). */
  private async loadSpotifyTrack(song: Song): Promise<void> {
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
      if (song.source === "local" && isMissingLocalFile(cause)) {
        // The bytes are gone (cleared site data, legacy record): remember it so
        // the row offers to re-link the file, instead of a raw error toast.
        useLocalFileStore.getState().markMissing(song.id);
        this.toast("error", "local.missingFile", { title: song.title });
        return;
      }
      this.fail(cause);
    }
  }

  // ------------------------------------------------------------ internals

  /** Send a transport request and mirror the answer into the live player. */
  private async commit(
    request: () => Promise<PlaybackState>,
    optimistic?: Partial<PlaybackState>,
  ): Promise<PlaybackState | null> {
    const before = this.identity();
    const state = await this.send(request, optimistic);
    if (state) await this.syncAfterState(state, before);
    return state;
  }

  /**
   * Send a transport request, mirroring the answer into the store.
   *
   * `optimistic` lands in the store immediately, so the UI reacts to the click
   * instead of to the round trip; a failed request restores the previous state
   * (and the live player). When the caller patched the store itself (to flip
   * it before the player even reacted), it passes the pre-patch state as
   * `rollbackTo` so the failure path still restores the truth. Answers apply
   * in initiation order: a response older than one already applied is dropped,
   * so a slow `report` can never undo a `next`. A `no_active_playback` answer
   * (the backend lost its context on restart) rebuilds it with a `select` and
   * retries once before giving up.
   */
  private async send(
    request: () => Promise<PlaybackState>,
    optimistic?: Partial<PlaybackState>,
    rollbackTo?: PlaybackState,
  ): Promise<PlaybackState | null> {
    const seq = ++this.requestSeq;
    const store = usePlaybackStore.getState();
    const snapshot = optimistic ? (rollbackTo ?? store.playback) : null;
    if (snapshot && optimistic && rollbackTo === undefined) {
      store.setPlayback({ ...snapshot, ...optimistic });
    }
    try {
      let state: PlaybackState;
      try {
        state = await request();
      } catch (cause) {
        if (!isNoActivePlayback(cause) || !(await this.rebuildContext())) throw cause;
        state = await request();
      }
      if (seq < this.lastAppliedSeq) return null; // a newer answer already won
      this.lastAppliedSeq = seq;
      usePlaybackStore.getState().setPlayback(state);
      return state;
    } catch (cause) {
      if (seq >= this.lastAppliedSeq) {
        if (snapshot && optimistic) this.rollback(snapshot, optimistic);
        this.fail(cause);
      }
      return null;
    }
  }

  /** Undo an optimistic patch after its request failed, player included. */
  private rollback(snapshot: PlaybackState, patch: Partial<PlaybackState>): void {
    usePlaybackStore.getState().setPlayback(snapshot);
    const player = this.player;
    if (!player || !snapshot.song || player.source !== snapshot.song.id) {
      return; // the song itself changed: the App effect reloads it from the snapshot
    }
    if (patch.position !== undefined) void player.seek(snapshot.position);
    if (patch.playing !== undefined) {
      if (snapshot.playing) void player.play();
      else player.pause();
    }
  }

  /**
   * State `next`/`previous` should show right away, built from the loaded queue.
   *
   * With shuffle off the edge flags and target indexes are recomputed exactly
   * like the backend does; with shuffle on the order is private to the server,
   * so only the song/index/position jump is optimistic and the flags stay stale
   * until the answer (one round trip) lands.
   */
  private targetPatch(key: "next_index" | "previous_index"): Partial<PlaybackState> | undefined {
    const playback = usePlaybackStore.getState().playback;
    const target = playback ? playback[key] : null;
    if (!playback || target === null || !playback.song) return undefined;
    const playlist = usePlaylistStore
      .getState()
      .playlists.find((item) => item.id === playback.playlist_id);
    const song = playlist?.songs[target];
    if (!song) return undefined; // queue not loaded: wait for the server answer

    const patch: Partial<PlaybackState> = { song, index: target, position: 0, playing: true };
    if (playback.shuffle || !playlist) return patch;

    const size = playlist.songs.length;
    const wrap = playback.repeat === "all" && size > 0;
    const atLast = target >= size - 1;
    const atFirst = target <= 0;
    return {
      ...patch,
      available_next: size > 0 && (!atLast || wrap),
      available_previous: size > 0 && (!atFirst || wrap),
      next_index: atLast ? (wrap ? 0 : null) : target + 1,
      previous_index: atFirst ? (wrap ? size - 1 : null) : target - 1,
    };
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
      if (state.playing) {
        if (this.userGesture) {
          await this.player.play();
        } else {
          // Autoplay policy: stay paused, wait for user gesture
          this.player.pause();
          this.toast("info", "autoplayBlocked");
        }
      } else {
        this.player.pause();
      }
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
        // Whole seconds only: the UI shows mm:ss, and a tick inside the same
        // second would re-render subscribers for nothing (`PERF-001`).
        if (Math.floor(prev.playback.position) === Math.floor(pos)) return prev;
        return { ...prev, playback: { ...prev.playback, position: pos, playing: true } };
      });
      this.scheduleReport(pos);
    });
    this.unsubscribeError = player.on("error", ({ payload }) => {
      const message = (payload as { error?: unknown; message?: string }).error
        ?? (payload as { message?: string }).message
        ?? "Unknown error";
      const msg = String(message);
      if (msg.includes("account_error") || msg.includes("Premium") || msg.includes("premium")) {
        this.toast("error", "spotify.premiumRequired");
      } else {
        this.fail(message);
      }
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
          if (isAutoplayBlocked(cause)) {
            // Autoplay policy: the reload restored a "playing" track with no
            // user gesture behind it. Load it paused, say why, and sync the
            // backend so the transport matches reality.
            player.pause();
            this.toast("info", "autoplayBlocked");
          } else {
            this.fail(cause);
          }
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
    if (this.unsubscribeError) {
      this.unsubscribeError();
      this.unsubscribeError = null;
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

  /** Recreate the backend playback context after it was lost (restart/spin-down). */
  private async rebuildContext(): Promise<boolean> {
    const playback = usePlaybackStore.getState().playback;
    if (!playback?.playlist_id || playback.index === null) return false;
    try {
      await this.api.selectSong(playback.playlist_id, playback.index);
      return true;
    } catch (cause) {
      if (cause instanceof ApiError && cause.code === "not_found") {
        await this.refresh(); // the playlist itself is gone: drop the dead state
      }
      return false;
    }
  }

  private toast(kind: "info" | "success" | "error", key: MessageKey, params?: Record<string, string | number>): void {
    useToastStore.getState().push(kind, translate(this.language(), key, params));
  }

  private fail(cause: unknown): void {
    const message = failureMessage(cause, this.language());
    useToastStore
      .getState()
      .push("error", translate(this.language(), "toast.error", { message }));
  }
}
