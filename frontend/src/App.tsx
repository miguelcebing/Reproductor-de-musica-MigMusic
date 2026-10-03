/** Main application container: wires controllers, stores and the UI. */

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiClient } from "./services/apiClient";
import { PlaylistController } from "./services/PlaylistController";
import { PlaybackController } from "./services/PlaybackController";
import { AuthController } from "./services/AuthController";
import { SpotifyController } from "./services/SpotifyController";
import { YouTubeController } from "./services/YouTubeController";
import { readCallbackParams } from "./services/callbackParams";
import { restoreObjectUrlsFromIndexedDB } from "./services/localFileUrls";
import { REPEAT_CYCLE } from "./ui/constants";
import { useT } from "./i18n/useT";
import { translate } from "./i18n/messages";
import { useSettingsStore, applyDocumentSettings } from "./state/settingsStore";
import { usePlaylistStore } from "./state/playlistStore";
import { usePlaybackStore } from "./state/playbackStore";
import { useSpotifyStore } from "./state/spotifyStore";
import { useYouTubeStore } from "./state/youtubeStore";
import { useAuthStore } from "./state/authStore";
import { useLocalFileStore } from "./state/localFileStore";
import { useToastStore } from "./state/toastStore";
import { AppShell } from "./ui/layouts/AppShell";
import { CoverArt } from "./ui/components/CoverArt";
import { NowPlaying } from "./ui/components/NowPlaying";
import { ProgressBar } from "./ui/components/ProgressBar";
import { PlayerControls } from "./ui/components/PlayerControls";
import { VolumeControl } from "./ui/components/VolumeControl";
import { TrackList } from "./ui/components/TrackList";
import { PlaylistBar } from "./ui/components/PlaylistBar";
import { SourceCard } from "./ui/components/SourceCard";
import { AddTrackDialog } from "./ui/components/AddTrackDialog";
import { LinkedListView } from "./ui/components/LinkedListView";
import { SpotifyCallback } from "./ui/components/SpotifyCallback";
import type { Song, TrackPosition } from "./domain/types";
import shellStyles from "./ui/layouts/AppShell.module.css";
import { BorderBeam } from "./ui/vengence/border-beam";
import playerStyles from "./ui/components/Player.module.css";

const EMPTY_SONGS: readonly Song[] = [];

export function App(): React.JSX.Element {
  const t = useT();

  // Settings
  const theme = useSettingsStore((s) => s.theme);
  const language = useSettingsStore((s) => s.language);
  const volume = useSettingsStore((s) => s.volume);
  const muted = useSettingsStore((s) => s.muted);
  const setTheme = useSettingsStore((s) => s.setTheme);
  const setLanguage = useSettingsStore((s) => s.setLanguage);
  const setVolume = useSettingsStore((s) => s.setVolume);
  const setMuted = useSettingsStore((s) => s.setMuted);

  // Playlists
  const playlists = usePlaylistStore((s) => s.playlists);
  const activeId = usePlaylistStore((s) => s.activeId);
  const loading = usePlaylistStore((s) => s.loading);
  const setActiveId = usePlaylistStore((s) => s.setActiveId);

  // Playback: field selectors, never the whole object — `position` ticks 1 Hz
  // and must not re-render this tree (the ProgressBar subscribes on its own).
  const playbackActive = usePlaybackStore((s) => s.playback !== null);
  const song = usePlaybackStore((s) => s.playback?.song ?? null);
  const playing = usePlaybackStore((s) => s.playback?.playing ?? false);
  const shuffle = usePlaybackStore((s) => s.playback?.shuffle ?? false);
  const repeat = usePlaybackStore((s) => s.playback?.repeat ?? "off");
  const playbackIndex = usePlaybackStore((s) => s.playback?.index ?? null);
  const playlistId = usePlaybackStore((s) => s.playback?.playlist_id ?? null);
  const skipSeconds = usePlaybackStore((s) => s.playback?.skip_seconds ?? 5);

  // Spotify link + catalog (`F6`)
  const spotifyStatus = useAuthStore((s) => s.status);
  const spotifyResults = useSpotifyStore((s) => s.results);
  const spotifyLoading = useSpotifyStore((s) => s.loading);

  // YouTube Music catalog (`F8`, keyless)
  const youtubeResults = useYouTubeStore((s) => s.results);
  const youtubeLoading = useYouTubeStore((s) => s.loading);

  // Toasts
  const toasts = useToastStore((s) => s.toasts);
  const dismissToast = useToastStore((s) => s.dismiss);

  // UI state
  const [nodesVisible, setNodesVisible] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  // Which tab the dialog opens on, so a source button jumps straight there.
  const [dialogTab, setDialogTab] = useState<"local" | "spotify" | "youtube">("local");

  // OAuth landing page (`F6`): decided once, before the first paint
  const callback = useMemo(
    () => readCallbackParams(window.location.pathname, window.location.search),
    [],
  );

  // Controllers (memoised once)
  const controllers = useMemo(() => {
    const api = ApiClient.fromOrigin(window.location.origin);
    const lang = () => useSettingsStore.getState().language;
    const playback = new PlaybackController(api, { language: lang });
    return {
      playlists: new PlaylistController(api, { language: lang, playbackController: playback }),
      playback,
      auth: new AuthController(api, { language: lang }),
      spotify: new SpotifyController(api, { language: lang }),
      youtube: new YouTubeController(api, { language: lang }),
    };
  }, []);

  // Keep document attributes in sync with the store
  useEffect(() => {
    applyDocumentSettings(theme, language);
  }, [theme, language]);

  // Keep Render awake while the tab is open: its free tier sleeps after
  // 15 min without traffic, and the next press would pay the cold start.
  useEffect(() => {
    const ping = () => {
      void fetch("/api/health", { cache: "no-store" }).catch(() => undefined);
    };
    const timer = setInterval(ping, 10 * 60_000);
    return () => clearInterval(timer);
  }, []);

  // Initial load: rebuild the local object URLs *before* the queue is read, so
  // `blob:` artwork URLs that died on reload are replaced, and tracks whose
  // bytes are gone are reported instead of failing silently (`LOCAL-006`).
  useEffect(() => {
    let cancelled = false;
    const bootstrap = async (): Promise<void> => {
      try {
        const report = await restoreObjectUrlsFromIndexedDB();
        if (!cancelled) useLocalFileStore.getState().setMissing(report.missing);
      } catch (cause) {
        const message = cause instanceof Error ? cause.message : String(cause);
        const language = useSettingsStore.getState().language;
        useToastStore.getState().push("error", translate(language, "toast.error", { message }));
      }
      if (cancelled) return;
      // Startup never resumes audio by itself: the queue is loaded, but the
      // player starts empty until the user presses play (autoplay policy and
      // a clean "nothing playing" screen).
      await Promise.all([
        controllers.playlists.refresh(),
        controllers.playback.refresh(/* restorePlaying */ false),
      ]);
      if (cancelled) return;
      usePlaybackStore.getState().reset();
    };
    void bootstrap();
    void controllers.auth.refresh();
    return () => {
      cancelled = true;
    };
  }, [controllers]);

  // Wire the player when the active track moves (F5/F7). Position ticks only
  // change `position`, so they re-render but never reload the audio; the song
  // identity (playlist + index + id) is what decides a reload.
  const songId = song?.id ?? null;
  const songIndex = playbackIndex;
  useEffect(() => {
    const current = usePlaybackStore.getState().playback;
    const unchanged =
      (current?.song?.id ?? null) === songId &&
      (current?.index ?? null) === songIndex &&
      (current?.playlist_id ?? null) === playlistId;
    if (unchanged) void controllers.playback.onTrackChange(current?.song ?? null);
  }, [controllers, songId, songIndex, playlistId]);

  // Derived state
  const activePlaylist = playlists.find((p) => p.id === activeId) ?? null;
  const currentIndex =
    playlistId && activePlaylist && playlistId === activePlaylist.id ? playbackIndex : null;
  const songs = activePlaylist?.songs ?? EMPTY_SONGS;
  const hasTrack = song != null;
  const duration = song?.duration ?? 0;

  // Event handlers
  const handleSelectPlaylist = useCallback(
    (id: string) => {
      setActiveId(id);
    },
    [setActiveId],
  );

  const handleCreatePlaylist = useCallback(
    (name: string) => {
      void controllers.playlists.create(name);
    },
    [controllers],
  );

  const handleRenamePlaylist = useCallback(
    (id: string, name: string) => {
      void controllers.playlists.rename(id, name);
    },
    [controllers],
  );

  const handleDeletePlaylist = useCallback(
    (id: string) => {
      void controllers.playlists.remove(id).then(() => {
        // Dropping the active playlist clears `activeId` even when others
        // remain; re-select one so the bar and the add button keep working.
        const store = usePlaylistStore.getState();
        if (store.activeId === null && store.playlists.length > 0) {
          store.setActiveId(store.playlists[0].id);
        }
      });
    },
    [controllers],
  );

  const handleOpenAddDialog = useCallback(() => {
    setDialogTab("local");
    setDialogOpen(true);
  }, []);

  const handleOpenDialogWithSource = useCallback(
    (source: "local" | "spotify" | "youtube") => {
      setDialogTab(source);
      setDialogOpen(true);
    },
    [],
  );

  /** Active playlist for a submit; picks the first one or creates a default. */
  const ensureActivePlaylist = useCallback(async (): Promise<string | null> => {
    const store = usePlaylistStore.getState();
    const current =
      store.activeId !== null && store.playlists.some((item) => item.id === store.activeId)
        ? store.activeId
        : null;
    if (current) return current;
    const first = store.playlists[0];
    if (first) {
      store.setActiveId(first.id);
      return first.id;
    }
    const created = await controllers.playlists.create(t("playlists.defaultName"));
    return created?.id ?? null;
  }, [controllers, t]);

  const handleSubmitTracks = useCallback(
    (files: File[], position: TrackPosition) => {
      void (async () => {
        const id = await ensureActivePlaylist();
        if (!id) return;
        await controllers.playlists.addLocalTracks(id, files, position);
      })();
    },
    [ensureActivePlaylist, controllers],
  );

  const handlePlayTrack = useCallback(
    (index: number) => {
      if (!activeId) return;
      void controllers.playback.select(activeId, index);
    },
    [activeId, controllers],
  );

  const handleRemoveTrack = useCallback(
    (index: number) => {
      if (!activeId) return;
      void controllers.playlists.removeSong(activeId, index);
    },
    [activeId, controllers],
  );

  const handleMoveTrack = useCallback(
    (index: number, delta: -1 | 1) => {
      if (!activeId) return;
      void controllers.playlists.moveSong(activeId, index, index + delta);
    },
    [activeId, controllers],
  );

  const handleFavoriteTrack = useCallback(
    (index: number, favorite: boolean) => {
      if (!activeId) return;
      void controllers.playlists.setFavorite(activeId, index, favorite);
    },
    [activeId, controllers],
  );

  const handleReorderTrack = useCallback(
    (fromIndex: number, toIndex: number) => {
      if (!activeId) return;
      void controllers.playlists.moveSong(activeId, fromIndex, toIndex);
    },
    [activeId, controllers],
  );

  const handleFindTrack = useCallback(
    (text: string): Promise<number | null> => {
      if (!activeId) return Promise.resolve(null);
      return controllers.playlists.findFirst(activeId, text);
    },
    [activeId, controllers],
  );

  const handleSeek = useCallback(
    (position: number) => {
      void controllers.playback.seek(position);
    },
    [controllers],
  );

  const handleTogglePlay = useCallback(() => {
    void controllers.playback.togglePlaying();
  }, [controllers]);

  const handleNext = useCallback(() => {
    void controllers.playback.next();
  }, [controllers]);

  const handlePrevious = useCallback(() => {
    void controllers.playback.previous();
  }, [controllers]);

  const handleSkip = useCallback(
    (direction: "forward" | "backward") => {
      void controllers.playback.skip(direction);
    },
    [controllers],
  );

  const handleToggleShuffle = useCallback(() => {
    void controllers.playback.toggleShuffle();
  }, [controllers]);

  const handleCycleRepeat = useCallback(() => {
    if (!playbackActive) return;
    const idx = REPEAT_CYCLE.indexOf(repeat);
    const next = REPEAT_CYCLE[(idx + 1) % REPEAT_CYCLE.length];
    void controllers.playback.setRepeat(next);
  }, [controllers, playbackActive, repeat]);

  const handleVolumeChange = useCallback(
    (v: number) => setVolume(v),
    [setVolume],
  );

  const handleToggleMute = useCallback(() => {
    setMuted(!muted);
  }, [muted, setMuted]);

  const handleSpotifyConnect = useCallback(() => {
    controllers.auth.login();
  }, [controllers]);

  const handleSpotifyDisconnect = useCallback(() => {
    void controllers.auth.logout();
  }, [controllers]);

  const handleSpotifySearch = useCallback(
    (query: string) => {
      void controllers.spotify.search(query);
    },
    [controllers],
  );

  const handleSubmitSpotify = useCallback(
    (songs: readonly Song[], position: TrackPosition) => {
      void (async () => {
        const id = await ensureActivePlaylist();
        if (!id) return;
        await controllers.playlists.addSongs(id, songs, position);
      })();
    },
    [ensureActivePlaylist, controllers],
  );

  const handleYouTubeSearch = useCallback(
    (query: string) => {
      void controllers.youtube.search(query);
    },
    [controllers],
  );

  const handleSubmitYouTube = useCallback(
    (songs: readonly Song[], position: TrackPosition) => {
      void (async () => {
        const id = await ensureActivePlaylist();
        if (!id) return;
        await controllers.playlists.addSongs(id, songs, position);
      })();
    },
    [ensureActivePlaylist, controllers],
  );

  const handleToggleTheme = useCallback(() => {
    setTheme(theme === "dark" ? "light" : "dark");
  }, [theme, setTheme]);

  const handleToggleLanguage = useCallback(() => {
    setLanguage(language === "es" ? "en" : "es");
  }, [language, setLanguage]);

  const handleToggleNodes = useCallback(() => {
    setNodesVisible((v) => !v);
  }, []);

  const handleCloseDialog = useCallback(() => {
    setDialogOpen(false);
  }, []);

  // OAuth callback: exchange the code and go back home (`F6`)
  if (callback) {
    return (
      <SpotifyCallback
        code={callback.code}
        state={callback.state}
        auth={controllers.auth}
      />
    );
  }

  return (
    <AppShell
      theme={theme}
      language={language}
      nodesVisible={nodesVisible}
      toasts={toasts}
      onToggleTheme={handleToggleTheme}
      onToggleLanguage={handleToggleLanguage}
      onToggleNodes={handleToggleNodes}
      onDismissToast={dismissToast}
    >
      <section
        className={`${shellStyles.card} ${shellStyles.playerCard}`}
        aria-label={t("player.play")}
      >
        <BorderBeam colorFrom="#7c3aed" colorTo="#a855f7" />
        <div className={playerStyles.player}>
          <CoverArt
            artworkUrl={song?.artwork_url ?? null}
            alt={song ? song.title : t("player.noTrack")}
            playing={playing}
          />
          <NowPlaying
            title={song ? song.title : t("player.noTrack")}
            artist={song ? song.artist : t("player.selectHint")}
          />
          <ProgressBar duration={duration} disabled={!hasTrack} step={skipSeconds} onSeek={handleSeek} />
          <PlayerControls
            playing={playing}
            disabled={!hasTrack}
            shuffle={shuffle}
            repeat={repeat}
            skipSeconds={skipSeconds}
            onTogglePlay={handleTogglePlay}
            onPrevious={handlePrevious}
            onNext={handleNext}
            onSkip={handleSkip}
            onToggleShuffle={handleToggleShuffle}
            onCycleRepeat={handleCycleRepeat}
          />
          <VolumeControl
            volume={volume}
            muted={muted}
            onVolume={handleVolumeChange}
            onToggleMute={handleToggleMute}
          />
        </div>
      </section>

      <section className={`${shellStyles.card} ${shellStyles.queueCard}`}>
        <PlaylistBar
          playlists={playlists}
          activeId={activeId}
          onSelect={handleSelectPlaylist}
          onCreate={handleCreatePlaylist}
          onRename={handleRenamePlaylist}
          onDelete={handleDeletePlaylist}
          onAddMusic={handleOpenAddDialog}
          onAddYouTube={() => handleOpenDialogWithSource("youtube")}
        />
        <TrackList
          songs={songs}
          currentIndex={currentIndex}
          loading={loading}
          onPlay={handlePlayTrack}
          onRemove={handleRemoveTrack}
          onMove={handleMoveTrack}
          onFavorite={handleFavoriteTrack}
          onReorder={handleReorderTrack}
          onFind={handleFindTrack}
          onAddMusic={handleOpenAddDialog}
        />
      </section>

      <section
        className={`${shellStyles.card} ${shellStyles.sourceCard}`}
        aria-label={t("source.title")}
      >
        <SourceCard
          trackCount={songs.length}
          spotifyConnected={spotifyStatus === "linked"}
          youtubeAvailable
          onAddFrom={handleOpenDialogWithSource}
          onSpotifyConnect={handleSpotifyConnect}
          onSpotifyDisconnect={handleSpotifyDisconnect}
        />
      </section>

      {nodesVisible && (
        <section
          className={`${shellStyles.card} ${shellStyles.nodesCard}`}
          aria-label={t("nodes.title")}
        >
          <h2 className={shellStyles.cardTitle}>{t("nodes.title")}</h2>
          <LinkedListView songs={songs} currentIndex={currentIndex} />
        </section>
      )}

      <AddTrackDialog
        open={dialogOpen}
        initialTab={dialogTab}
        songsLength={songs.length}
        spotifyConnected={spotifyStatus === "linked"}
        spotifyLoading={spotifyLoading}
        spotifyResults={spotifyResults}
        youtubeAvailable
        youtubeLoading={youtubeLoading}
        youtubeResults={youtubeResults}
        onClose={handleCloseDialog}
        onSubmit={handleSubmitTracks}
        onSubmitSpotify={handleSubmitSpotify}
        onSubmitYouTube={handleSubmitYouTube}
        onSpotifySearch={handleSpotifySearch}
        onSpotifyConnect={handleSpotifyConnect}
        onSpotifyDisconnect={handleSpotifyDisconnect}
        onYouTubeSearch={handleYouTubeSearch}
      />
    </AppShell>
  );
}