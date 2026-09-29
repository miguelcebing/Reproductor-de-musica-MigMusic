/** Main application container: wires controllers, stores and the UI. */

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiClient } from "./services/apiClient";
import { PlaylistController } from "./services/PlaylistController";
import { PlaybackController } from "./services/PlaybackController";
import { REPEAT_CYCLE } from "./ui/constants";
import { useT } from "./i18n/useT";
import { useSettingsStore, applyDocumentSettings } from "./state/settingsStore";
import { usePlaylistStore } from "./state/playlistStore";
import { usePlaybackStore } from "./state/playbackStore";
import { useToastStore } from "./state/toastStore";
import { AppShell } from "./ui/layouts/AppShell";
import { CoverArt } from "./ui/components/CoverArt";
import { NowPlaying } from "./ui/components/NowPlaying";
import { ProgressBar } from "./ui/components/ProgressBar";
import { PlayerControls } from "./ui/components/PlayerControls";
import { VolumeControl } from "./ui/components/VolumeControl";
import { TrackList } from "./ui/components/TrackList";
import { PlaylistBar } from "./ui/components/PlaylistBar";
import { AddTrackDialog } from "./ui/components/AddTrackDialog";
import { LinkedListView } from "./ui/components/LinkedListView";
import type { TrackPosition } from "./domain/types";
import shellStyles from "./ui/layouts/AppShell.module.css";
import playerStyles from "./ui/components/Player.module.css";

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

  // Playback
  const playback = usePlaybackStore((s) => s.playback);

  // Toasts
  const toasts = useToastStore((s) => s.toasts);
  const dismissToast = useToastStore((s) => s.dismiss);

  // UI state
  const [nodesVisible, setNodesVisible] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Controllers (memoised once)
  const controllers = useMemo(() => {
    const api = ApiClient.fromOrigin(window.location.origin);
    const lang = () => useSettingsStore.getState().language;
    return {
      playlists: new PlaylistController(api, { language: lang }),
      playback: new PlaybackController(api, { language: lang }),
    };
  }, []);

  // Keep document attributes in sync with the store
  useEffect(() => {
    applyDocumentSettings(theme, language);
  }, [theme, language]);

  // Initial load
  useEffect(() => {
    void controllers.playlists.refresh();
    void controllers.playback.refresh();
  }, [controllers]);

  // Derived state
  const activePlaylist = playlists.find((p) => p.id === activeId) ?? null;
  const currentIndex =
    playback && activePlaylist && playback.playlist_id === activePlaylist.id
      ? playback.index
      : null;
  const songs = activePlaylist?.songs ?? [];
  const skipSeconds = playback?.skip_seconds ?? 5;
  const hasTrack = playback?.song !== null;
  const duration = playback?.song?.duration ?? 0;
  const progressLabel = t("player.time", {
    current: Math.round(playback?.position ?? 0),
    total: Math.round(duration),
  });

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
      void controllers.playlists.remove(id);
    },
    [controllers],
  );

  const handleOpenAddDialog = useCallback(() => {
    if (activeId) setDialogOpen(true);
  }, [activeId]);

  const handleSubmitTracks = useCallback(
    (files: File[], position: TrackPosition) => {
      if (!activeId) return;
      void controllers.playlists.addLocalTracks(activeId, files, position);
    },
    [activeId, controllers],
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
    if (!playback) return;
    const current = playback.repeat;
    const idx = REPEAT_CYCLE.indexOf(current);
    const next = REPEAT_CYCLE[(idx + 1) % REPEAT_CYCLE.length];
    void controllers.playback.setRepeat(next);
  }, [controllers, playback]);

  const handleVolumeChange = useCallback(
    (v: number) => setVolume(v),
    [setVolume],
  );

  const handleToggleMute = useCallback(() => {
    setMuted(!muted);
  }, [muted, setMuted]);

  return (
    <AppShell
      theme={theme}
      language={language}
      nodesVisible={nodesVisible}
      toasts={toasts}
      onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
      onToggleLanguage={() => setLanguage(language === "es" ? "en" : "es")}
      onToggleNodes={() => setNodesVisible((v) => !v)}
      onDismissToast={dismissToast}
    >
      <section className={shellStyles.card} aria-label={t("player.play")}>
        <div className={playerStyles.player}>
          <CoverArt
            artworkUrl={playback?.song?.artwork_url ?? null}
            alt={hasTrack ? playback!.song!.title : t("player.noTrack")}
            playing={playback?.playing ?? false}
          />
          <NowPlaying
            title={hasTrack ? playback!.song!.title : t("player.noTrack")}
            artist={hasTrack ? playback!.song!.artist : t("player.selectHint")}
          />
          <ProgressBar
            position={playback?.position ?? 0}
            duration={duration}
            disabled={!hasTrack}
            step={skipSeconds}
            label={progressLabel}
            onSeek={handleSeek}
          />
          <PlayerControls
            playing={playback?.playing ?? false}
            disabled={!hasTrack}
            canPrevious={playback?.available_previous ?? false}
            canNext={playback?.available_next ?? false}
            shuffle={playback?.shuffle ?? false}
            repeat={playback?.repeat ?? "off"}
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

      <section className={shellStyles.card}>
        <PlaylistBar
          playlists={playlists}
          activeId={activeId}
          onSelect={handleSelectPlaylist}
          onCreate={handleCreatePlaylist}
          onRename={handleRenamePlaylist}
          onDelete={handleDeletePlaylist}
          onAddMusic={handleOpenAddDialog}
        />
        <TrackList
          songs={songs}
          currentIndex={currentIndex}
          loading={loading}
          onPlay={handlePlayTrack}
          onRemove={handleRemoveTrack}
          onMove={handleMoveTrack}
        />
        {nodesVisible && <LinkedListView songs={songs} currentIndex={currentIndex} />}
      </section>

      <AddTrackDialog
        open={dialogOpen}
        songsLength={songs.length}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmitTracks}
      />
    </AppShell>
  );
}