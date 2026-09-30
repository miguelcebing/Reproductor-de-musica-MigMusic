/** Queue rows: cover, duration, source badge, heart and row actions (`UX-001`). */

import type { DragEvent } from "react";

import type { Song } from "../../domain/types";
import { useT } from "../../i18n/useT";
import { formatTime } from "../utils/format";
import styles from "./Queue.module.css";
import { DownIcon, HeartIcon, TrashIcon, UpIcon } from "./icons";

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
    <li
      className={classes}
      data-testid="track-row"
      data-index={index}
      data-active={isActive}
      data-match={isMatch}
      aria-current={isActive ? "true" : undefined}
      draggable
      onDragStart={drag.onDragStart}
      onDragOver={drag.onDragOver}
      onDrop={drag.onDrop}
      onDragEnd={drag.onDragEnd}
      onDragLeave={drag.onDragLeave}
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
    </li>
  );
}
