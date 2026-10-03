/** Playlist selector with create / rename / delete (`PLAYLIST-001 = B`). */

import { memo, useState } from "react";

import type { Playlist } from "../../domain/types";
import { useT } from "../../i18n/useT";
import styles from "./Queue.module.css";

export interface PlaylistBarProps {
  readonly playlists: readonly Playlist[];
  readonly activeId: string | null;
  readonly onSelect: (id: string) => void;
  readonly onCreate: (name: string) => void;
  readonly onRename: (id: string, name: string) => void;
  readonly onDelete: (id: string) => void;
  readonly onAddMusic: () => void;
  /** Quick entry point to the YouTube Music tab. */
  readonly onAddYouTube?: () => void;
}

export const PlaylistBar = memo(function PlaylistBar({
  playlists,
  activeId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
  onAddMusic,
  onAddYouTube,
}: PlaylistBarProps): React.JSX.Element {
  const t = useT();
  const [name, setName] = useState("");

  const trimmed = name.trim();

  return (
    <div className={styles.playlistBar}>
      <select
        className={styles.select}
        value={activeId ?? ""}
        aria-label={t("playlists.label")}
        data-testid="playlist-select"
        onChange={(event) => onSelect(event.target.value)}
      >
        {playlists.length === 0 && <option value="">{t("list.emptyTitle")}</option>}
        {playlists.map((playlist) => (
          <option key={playlist.id} value={playlist.id}>
            {playlist.name} · {t("playlists.count", { count: playlist.size })}
          </option>
        ))}
      </select>

      <input
        className={styles.input}
        type="text"
        value={name}
        placeholder={t("playlists.placeholder")}
        aria-label={t("playlists.placeholder")}
        data-testid="playlist-name"
        onChange={(event) => setName(event.target.value)}
      />

      <button
        type="button"
        className={styles.button}
        disabled={trimmed.length === 0}
        onClick={() => {
          onCreate(trimmed);
          setName("");
        }}
        data-testid="playlist-create"
      >
        {t("playlists.create")}
      </button>

      <button
        type="button"
        className={styles.button}
        disabled={!activeId || trimmed.length === 0}
        onClick={() => {
          if (activeId) onRename(activeId, trimmed);
          setName("");
        }}
      >
        {t("playlists.rename")}
      </button>

      <button
        type="button"
        className={styles.button}
        disabled={!activeId}
        onClick={() => activeId && onDelete(activeId)}
        data-testid="playlist-delete"
      >
        {t("playlists.delete")}
      </button>

      {onAddYouTube && (
        <button
          type="button"
          className={styles.button}
          onClick={onAddYouTube}
          data-testid="add-youtube"
          title={t("source.youtube")}
        >
          {t("source.youtube")}
        </button>
      )}

      <button
        type="button"
        className={`${styles.button} ${styles.buttonPrimary}`}
        onClick={onAddMusic}
        data-testid="add-music"
      >
        {t("dialog.addTitle")}
      </button>
    </div>
  );
});
