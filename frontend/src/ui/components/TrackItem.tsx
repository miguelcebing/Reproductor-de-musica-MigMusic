/** Queue rows: small cover, duration, source badge and row actions (`UX-001`). */

import type { Song } from "../../domain/types";
import { useT } from "../../i18n/useT";
import { formatTime } from "../utils/format";
import styles from "./Queue.module.css";
import { DownIcon, TrashIcon, UpIcon } from "./icons";

export interface TrackItemProps {
  readonly song: Song;
  readonly index: number;
  readonly isActive: boolean;
  readonly canMoveUp: boolean;
  readonly canMoveDown: boolean;
  readonly onPlay: () => void;
  readonly onRemove: () => void;
  readonly onMove: (delta: -1 | 1) => void;
}

export function TrackItem({
  song,
  index,
  isActive,
  canMoveUp,
  canMoveDown,
  onPlay,
  onRemove,
  onMove,
}: TrackItemProps): React.JSX.Element {
  const t = useT();

  return (
    <li
      className={`${styles.row} ${isActive ? styles.rowCurrent : ""}`}
      data-testid="track-row"
      data-index={index}
      data-active={isActive}
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
