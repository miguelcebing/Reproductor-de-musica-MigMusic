/** Queue rows: cover, duration, source badge, heart and row actions (`UX-001`).

 * A local track whose bytes are gone (cleared site data, legacy record) shows
 * a re-link action instead of failing on play (`LOCAL-006`).
 */

import { useRef, type DragEvent } from "react";
import { motion } from "framer-motion";

import type { Song } from "../../domain/types";
import { useT } from "../../i18n/useT";
import { relinkLocalTrack } from "../../services/localTracks";
import { useLocalFileStore } from "../../state/localFileStore";
import { useToastStore } from "../../state/toastStore";
import { formatTime } from "../utils/format";
import styles from "./Queue.module.css";
import { DownIcon, HeartIcon, LinkIcon, TrashIcon, UpIcon } from "./icons";

/** Drag wiring owned by `TrackList`; every row forwards it to its `<li>`. */
export interface RowDragProps {
  readonly isDragging: boolean;
  readonly isDragOver: boolean;
  readonly onDragStart: (event: DragEvent<HTMLLIElement>) => void;
  readonly onDragOver: (event: DragEvent<HTMLLIElement>) => void;
  readonly onDrop: (event: DragEvent<HTMLLIElement>) => void;
  readonly onDragEnd: () => void;
  readonly onDragLeave: () => void;
}

export interface TrackItemProps {
  readonly song: Song;
  readonly index: number;
  readonly isActive: boolean;
  readonly isMatch: boolean;
  readonly canMoveUp: boolean;
  readonly canMoveDown: boolean;
  readonly onPlay: () => void;
  readonly onRemove: () => void;
  readonly onMove: (delta: -1 | 1) => void;
  readonly onFavorite: () => void;
  readonly drag: RowDragProps;
}

export function TrackItem({
  song,
  index,
  isActive,
  isMatch,
  canMoveUp,
  canMoveDown,
  onPlay,
  onRemove,
  onMove,
  onFavorite,
  drag,
}: TrackItemProps): React.JSX.Element {
  const t = useT();
  const missingFile = useLocalFileStore((state) =>
    song.source === "local" ? state.missing.includes(song.id) : false,
  );
  const relinkRef = useRef<HTMLInputElement>(null);

  const handleRelink = async (file: File): Promise<void> => {
    try {
      const linked = await relinkLocalTrack(song.id, file);
      if (!linked) throw new Error("track not found");
      useLocalFileStore.getState().markPresent(song.id);
      useToastStore.getState().push("success", t("local.relinked"));
    } catch {
      useToastStore.getState().push("error", t("local.relinkFailed"));
    }
  };

  const classes = [
    styles.row,
    isActive ? styles.rowCurrent : "",
    isMatch ? styles.rowMatch : "",
    drag.isDragging ? styles.rowDragging : "",
    drag.isDragOver ? styles.rowDropTarget : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <motion.li
      className={classes}
      data-testid="track-row"
      data-index={index}
      data-active={isActive}
      data-match={isMatch}
      aria-current={isActive ? "true" : undefined}
      draggable
      onDragStartCapture={drag.onDragStart}
      onDragOver={drag.onDragOver}
      onDrop={drag.onDrop}
      onDragEndCapture={drag.onDragEnd}
      onDragLeave={drag.onDragLeave}
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: drag.isDragging ? 0.5 : 1, y: 0 }}
      exit={{ opacity: 0, x: 24 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
    >
      {song.artwork_url ? (
        <img
          className={styles.rowCover}
          src={song.artwork_url}
          alt=""
          width={44}
          height={44}
          loading="lazy"
          decoding="async"
        />
      ) : (
        <span className={styles.rowCover} aria-hidden="true">
          ♪
        </span>
      )}

      <div className={styles.rowMain}>
        <button type="button" className={styles.rowTitle} onClick={onPlay} aria-label={t("list.play", { title: song.title })}>
          {song.title}
        </button>
        <p className={styles.rowMeta}>
          <span>{song.artist || "—"}</span>
          <span className={styles.badge}>{t(`source.${song.source}`)}</span>
        </p>
      </div>

      <div className={styles.rowActions}>
        <span className={styles.duration}>{song.duration_label || formatTime(song.duration)}</span>
        {missingFile && (
          <>
            <input
              ref={relinkRef}
              type="file"
              accept="audio/*"
              hidden
              data-testid={`relink-input-${index}`}
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (file) void handleRelink(file);
              }}
            />
            <button
              type="button"
              className={styles.button}
              onClick={() => relinkRef.current?.click()}
              aria-label={t("local.relink", { title: song.title })}
              title={t("local.relink", { title: song.title })}
              data-testid={`relink-${index}`}
            >
              <LinkIcon width={16} height={16} />
            </button>
          </>
        )}
        <button
          type="button"
          className={`${styles.button} ${song.favorite ? styles.buttonFavorite : ""}`}
          onClick={onFavorite}
          aria-pressed={song.favorite}
          aria-label={t(song.favorite ? "list.unfavorite" : "list.favorite", { title: song.title })}
          data-testid={`favorite-${index}`}
        >
          {song.favorite ? (
            <HeartIcon width={16} height={16} />
          ) : (
            <HeartIcon width={16} height={16} fill="none" stroke="currentColor" strokeWidth={2} strokeLinejoin="round" />
          )}
        </button>
        <button
          type="button"
          className={styles.button}
          onClick={() => onMove(-1)}
          disabled={!canMoveUp}
          aria-label={t("list.moveUp", { title: song.title })}
        >
          <UpIcon width={16} height={16} />
        </button>
        <button
          type="button"
          className={styles.button}
          onClick={() => onMove(1)}
          disabled={!canMoveDown}
          aria-label={t("list.moveDown", { title: song.title })}
        >
          <DownIcon width={16} height={16} />
        </button>
        <button
          type="button"
          className={styles.button}
          onClick={onRemove}
          aria-label={t("list.remove", { title: song.title })}
          data-testid={`remove-${index}`}
        >
          <TrashIcon width={16} height={16} />
        </button>
      </div>
    </motion.li>
  );
}
