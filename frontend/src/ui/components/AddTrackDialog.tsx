/** Add-music modal with Local/Spotify tabs and a position picker (`UX-003`).

 * The Spotify tab searches the catalog (`SPOTIFY-006`) when the session is
 * linked; otherwise it offers the OAuth login. Results are ticked and added
 * in bulk to the active playlist.
 */

import { memo, useEffect, useState } from "react";
import {
  Button,
  ModalBackdrop,
  ModalBody,
  ModalCloseTrigger,
  ModalContainer,
  ModalDialog,
  ModalFooter,
  ModalHeader,
  ModalHeading,
  ModalRoot,
  Tab,
  TabList,
  TabPanel,
  TabsRoot,
} from "@heroui/react";

import type { Song, TrackPosition } from "../../domain/types";
import { isSupportedAudioFile } from "../../services/localTracks";
import { useT } from "../../i18n/useT";
import styles from "./Queue.module.css";
import { SpotifyIcon } from "./icons";

export type { TrackPosition };

export interface AddTrackDialogProps {
  readonly open: boolean;
  /** Tab the dialog opens on; lets a source button jump straight to it. */
  readonly initialTab?: "local" | "spotify" | "youtube";
  readonly songsLength: number;
  readonly spotifyConnected: boolean;
  readonly spotifyLoading: boolean;
  readonly spotifyResults: readonly Song[];
  readonly youtubeAvailable?: boolean;
  readonly youtubeLoading?: boolean;
  readonly youtubeResults?: readonly Song[];
  readonly onClose: () => void;
  readonly onSubmit: (files: File[], position: TrackPosition) => void;
  readonly onSubmitSpotify: (songs: readonly Song[], position: TrackPosition) => void;
  readonly onSubmitYouTube?: (songs: readonly Song[], position: TrackPosition) => void;
  readonly onSpotifySearch: (query: string) => void;
  readonly onSpotifyConnect: () => void;
  readonly onSpotifyDisconnect: () => void;
  readonly onYouTubeSearch?: (query: string) => void;
}

export const AddTrackDialog = memo(function AddTrackDialog({
  open,
  initialTab = "local",
  songsLength,
  spotifyConnected,
  spotifyLoading,
  spotifyResults,
  youtubeAvailable = false,
  youtubeLoading = false,
  youtubeResults = [],
  onClose,
  onSubmit,
  onSubmitSpotify,
  onSubmitYouTube,
  onSpotifySearch,
  onSpotifyConnect,
  onSpotifyDisconnect,
  onYouTubeSearch,
}: AddTrackDialogProps): React.JSX.Element {
  const t = useT();
  const [tab, setTab] = useState<"local" | "spotify" | "youtube">("local");
  const [files, setFiles] = useState<readonly File[]>([]);
  const [positionKind, setPositionKind] = useState<"start" | "end" | "index">("end");
  const [index, setIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());
  const [searched, setSearched] = useState(false);

  // Escape, outside press and focus containment come from the modal primitive.
  const handleOpenChange = (nextOpen: boolean): void => {
    if (!nextOpen) onClose();
  };

  // A fresh search (either catalog) invalidates the previous selection.
  useEffect(() => {
    setSelected(new Set());
  }, [spotifyResults, youtubeResults]);

  // Opening jumps to the requested source tab; closing resets everything.
  useEffect(() => {
    if (open) {
      setTab(initialTab);
      return;
    }
    setQuery("");
    setSearched(false);
    setSelected(new Set());
    setError(null);
    setFiles([]);
    setTab("local");
  }, [open, initialTab]);

  const maxIndex = Math.max(0, songsLength - 1);
  const boundedIndex = Math.min(index, maxIndex);
  const pendingCount = tab === "local" ? files.length : selected.size;

  const position: TrackPosition =
    positionKind === "start"
      ? { kind: "start" }
      : positionKind === "index"
        ? { kind: "index", index: boundedIndex }
        : { kind: "end" };

  const submitLocal = (): void => {
    if (files.length === 0) {
      setError(t("dialog.noFiles"));
      return;
    }
    const accepted = files.filter(isSupportedAudioFile);
    if (accepted.length !== files.length) {
      setError(t("dialog.invalidFiles"));
      return;
    }
    onSubmit(accepted, position);
    setFiles([]);
    setError(null);
    onClose();
  };

  const submitSpotify = (): void => {
    const chosen = spotifyResults.filter((song) => selected.has(song.id));
    if (chosen.length === 0) {
      setError(t("spotify.selectOne"));
      return;
    }
    onSubmitSpotify(chosen, position);
    setError(null);
    onClose();
  };

  const submitYouTube = (): void => {
    const chosen = youtubeResults.filter((song) => selected.has(song.id));
    if (chosen.length === 0) {
      setError(t("youtube.selectOne"));
      return;
    }
    onSubmitYouTube?.(chosen, position);
    setError(null);
    onClose();
  };

  const submit = (): void => {
    if (tab === "spotify") {
      if (spotifyConnected) submitSpotify();
      else onSpotifyConnect();
      return;
    }
    if (tab === "youtube") {
      submitYouTube();
      return;
    }
    submitLocal();
  };

  const toggleSelected = (id: string): void => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const runSearch = (event: React.FormEvent): void => {
    event.preventDefault();
    setSearched(true);
    onSpotifySearch(query);
  };

  const runYouTubeSearch = (event: React.FormEvent): void => {
    event.preventDefault();
    setSearched(true);
    onYouTubeSearch?.(query);
  };

  const showPositionPicker = tab === "local" || spotifyConnected || tab === "youtube";

  return (
    <ModalRoot isOpen={open} onOpenChange={handleOpenChange}>
      <ModalBackdrop>
        <ModalContainer placement="center" scroll="inside" size="lg">
          <ModalDialog className={styles.dialog} data-testid="add-dialog">
            <ModalHeader className={styles.dialogHeader}>
              <ModalHeading className={styles.dialogTitle}>
                {t("dialog.addTitle")}
              </ModalHeading>
              <ModalCloseTrigger
                aria-label={t("dialog.close")}
                className={styles.dialogClose}
                data-testid="dialog-close"
              />
            </ModalHeader>

            <TabsRoot
              className={styles.tabsRoot}
              selectedKey={tab}
              onSelectionChange={(key) => {
                if (key === "spotify") setTab("spotify");
                else if (key === "youtube") setTab("youtube");
                else setTab("local");
              }}
            >
              <TabList className={styles.tabs}>
                <Tab
                  id="local"
                  className={`${styles.tab} ${tab === "local" ? styles.tabActive : ""}`}
                  data-testid="tab-local"
                >
                  {t("dialog.tabLocal")}
                </Tab>
                <Tab
                  id="spotify"
                  className={`${styles.tab} ${tab === "spotify" ? styles.tabActive : ""}`}
                  data-testid="tab-spotify"
                >
                  {t("dialog.tabSpotify")}
                </Tab>
                <Tab
                  id="youtube"
                  className={`${styles.tab} ${tab === "youtube" ? styles.tabActive : ""}`}
                  data-testid="tab-youtube"
                >
                  {t("dialog.tabYouTube")}
                </Tab>
              </TabList>

              {/* Scrollable middle: the action row stays pinned below it, so the
                  submit button is never pushed off-screen by long results. */}
              <ModalBody className={styles.dialogBody}>
                <TabPanel id="local" className={styles.tabPanel}>
                  <label className={styles.field}>
                    {t("dialog.files")}
                    <input
                      type="file"
                      multiple
                      accept="audio/mpeg,audio/wav,.mp3,.wav"
                      data-testid="file-input"
                      onChange={(event) => {
                        setFiles(Array.from(event.target.files ?? []));
                        setError(null);
                      }}
                    />
                  </label>
                  <p className={styles.hint}>{t("dialog.filesHint")}</p>
                </TabPanel>

                <TabPanel id="spotify" className={styles.tabPanel}>
                  {spotifyConnected ? (
                    <>
                      <form className={styles.playlistBar} onSubmit={runSearch}>
                        <input
                          type="search"
                          className={styles.input}
                          value={query}
                          placeholder={t("spotify.searchPlaceholder")}
                          aria-label={t("spotify.search")}
                          data-testid="spotify-query"
                          onChange={(event) => setQuery(event.target.value)}
                        />
                        <button
                          type="submit"
                          className={styles.button}
                          disabled={spotifyLoading}
                          data-testid="spotify-search"
                        >
                          {spotifyLoading ? t("spotify.searching") : t("spotify.search")}
                        </button>
                      </form>
                      <p className={styles.hint}>{t("spotify.selectHint")}</p>
                      {spotifyLoading ? (
                        <p className={styles.loading} data-testid="spotify-loading">
                          {t("spotify.searching")}
                        </p>
                      ) : spotifyResults.length === 0 ? (
                        <p className={styles.hint} data-testid="spotify-empty">
                          {searched ? t("spotify.noResults") : ""}
                        </p>
                      ) : (
                        <ul className={styles.list} data-testid="spotify-results">
                          {spotifyResults.map((song) => (
                            <li key={song.id} className={styles.row}>
                              <input
                                type="checkbox"
                                className={styles.rowCheck}
                                checked={selected.has(song.id)}
                                aria-label={`${song.title} - ${song.artist}`}
                                onChange={() => toggleSelected(song.id)}
                                data-testid={`spotify-result-${song.id}`}
                              />
                              <div className={styles.rowMain}>
                                <p className={styles.rowTitle}>{song.title}</p>
                                <p className={styles.rowMeta}>{song.artist}</p>
                              </div>
                              <span className={styles.duration}>{song.duration_label}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                      <p className={styles.count}>
                        {t("spotify.results", { count: spotifyResults.length })}
                      </p>
                      <button
                        type="button"
                        className={styles.button}
                        onClick={onSpotifyDisconnect}
                        data-testid="spotify-disconnect"
                      >
                        {t("spotify.disconnect")}
                      </button>
                    </>
                  ) : (
                    <div
                      className={styles.spotifyDisconnected}
                      data-testid="spotify-disconnected"
                    >
                      <div className={styles.spotifyDisconnectedIcon}>
                        <SpotifyIcon width={48} height={48} />
                      </div>
                      <h3 className={styles.spotifyDisconnectedTitle}>
                        {t("dialog.spotifyMissing")}
                      </h3>
                      <p className={styles.spotifyDisconnectedDesc}>
                        {t("dialog.spotifyMissingDesc")}
                      </p>
                      <button
                        type="button"
                        className={`${styles.button} ${styles.buttonPrimary} ${styles.spotifyConnectBtn}`}
                        onClick={onSpotifyConnect}
                        data-testid="spotify-connect"
                      >
                        <SpotifyIcon width={18} height={18} />
                        {t("spotify.connect")}
                      </button>
                      <p className={styles.spotifyDisconnectedNote}>
                        {t("dialog.spotifyPremiumNote")}
                      </p>
                    </div>
                  )}
                </TabPanel>

                <TabPanel id="youtube" className={styles.tabPanel}>
                  {youtubeAvailable ? (
                    <>
                      <form className={styles.playlistBar} onSubmit={runYouTubeSearch}>
                        <input
                          type="search"
                          className={styles.input}
                          value={query}
                          placeholder={t("youtube.searchPlaceholder")}
                          aria-label={t("youtube.search")}
                          data-testid="youtube-query"
                          onChange={(event) => setQuery(event.target.value)}
                        />
                        <button
                          type="submit"
                          className={styles.button}
                          disabled={youtubeLoading}
                          data-testid="youtube-search"
                        >
                          {youtubeLoading ? t("youtube.searching") : t("youtube.search")}
                        </button>
                      </form>
                      <p className={styles.hint}>{t("youtube.selectHint")}</p>
                      {youtubeLoading ? (
                        <p className={styles.loading} data-testid="youtube-loading">
                          {t("youtube.searching")}
                        </p>
                      ) : youtubeResults.length === 0 ? (
                        <p className={styles.hint} data-testid="youtube-empty">
                          {searched ? t("youtube.noResults") : ""}
                        </p>
                      ) : (
                        <ul className={styles.list} data-testid="youtube-results">
                          {youtubeResults.map((song) => (
                            <li key={song.id} className={styles.row}>
                              <input
                                type="checkbox"
                                className={styles.rowCheck}
                                checked={selected.has(song.id)}
                                aria-label={`${song.title} - ${song.artist}`}
                                onChange={() => toggleSelected(song.id)}
                                data-testid={`youtube-result-${song.id}`}
                              />
                              <div className={styles.rowMain}>
                                <p className={styles.rowTitle}>{song.title}</p>
                                <p className={styles.rowMeta}>{song.artist}</p>
                              </div>
                              <span className={styles.duration}>{song.duration_label}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                      <p className={styles.count}>
                        {t("youtube.results", { count: youtubeResults.length })}
                      </p>
                    </>
                  ) : (
                    <p className={styles.hint} data-testid="youtube-unavailable">
                      {t("youtube.notConfigured")}
                    </p>
                  )}
                </TabPanel>

                {showPositionPicker && (
                  <fieldset className={styles.field}>
                    <legend>{t("dialog.position")}</legend>
                    <div className={styles.positions}>
                      {(["start", "end", "index"] as const).map((kind) => (
                        <button
                          key={kind}
                          type="button"
                          className={`${styles.position} ${
                            positionKind === kind ? styles.positionActive : ""
                          }`}
                          aria-pressed={positionKind === kind}
                          onClick={() => setPositionKind(kind)}
                          data-testid={`position-${kind}`}
                        >
                          {kind === "start"
                            ? t("dialog.positionStart")
                            : kind === "end"
                              ? t("dialog.positionEnd")
                              : t("dialog.positionIndex")}
                        </button>
                      ))}
                    </div>
                    {positionKind === "index" && (
                      <input
                        type="number"
                        min={0}
                        max={maxIndex}
                        value={boundedIndex}
                        aria-label={t("dialog.positionIndex")}
                        onChange={(event) => setIndex(Number(event.target.value))}
                      />
                    )}
                  </fieldset>
                )}

                {error && (
                  <p className={styles.error} role="alert">
                    {error}
                  </p>
                )}
              </ModalBody>
            </TabsRoot>

            <ModalFooter className={styles.dialogActions}>
              <Button
                variant="ghost"
                onPress={onClose}
                data-testid="dialog-cancel"
              >
                {t("dialog.cancel")}
              </Button>
              <Button
                variant="primary"
                onPress={submit}
                data-testid="dialog-submit"
              >
                {tab === "spotify" && !spotifyConnected
                  ? t("spotify.connect")
                  : pendingCount > 0
                    ? t("dialog.submitCount", { count: pendingCount })
                    : t("dialog.submit")}
              </Button>
            </ModalFooter>
          </ModalDialog>
        </ModalContainer>
      </ModalBackdrop>
    </ModalRoot>
  );
});
