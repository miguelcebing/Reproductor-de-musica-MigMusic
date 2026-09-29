/** The queue: loading, empty and populated states (`UX-004`, `TEST-002`). */

import { useState } from "react";

import type { Song } from "../../domain/types";
import { useT } from "../../i18n/useT";
import { EmptyState } from "./EmptyState";
import { TrackItem } from "./TrackItem";
import styles from "./Queue.module.css";

export interface TrackListProps {
  readonly songs: readonly Song[];
  readonly currentIndex: number | null;
  readonly loading: boolean;
  readonly onPlay: (index: number) => void;
  readonly onRemove: (index: number) => void;
  readonly onMove: (index: number, delta: -1 | 1) => void;
}

export function TrackList({
  songs,
  currentIndex,
  loading,
  onPlay,
  onRemove,
  onMove,
}: TrackListProps): React.JSX.Element {
  const t = useT();
  const [query, setQuery] = useState("");

  if (loading) {
    return <p className={styles.loading}>{t("list.loading")}</p>;
  }

  const normalized = query.trim().toLowerCase();
  const visible = normalized
    ? songs
        .map((song, index) => ({ song, index }))
        .filter(
          ({ song }) =>
            song.title.toLowerCase().includes(normalized) ||
            song.artist.toLowerCase().includes(normalized),
        )
    : songs.map((song, index) => ({ song, index }));

  if (songs.length === 0) {
    return <EmptyState title={t("list.emptyTitle")} body={t("list.emptyBody")} />;
  }

  return (
    <section aria-label={t("list.title")}>
      <input
        className={`${styles.input} ${styles.search}`}
        type="search"
        value={query}
        placeholder={t("list.search")}
        aria-label={t("list.search")}
        data-testid="track-search"
        onChange={(event) => setQuery(event.target.value)}
      />
      <p className={styles.count}>{t("list.results", { shown: visible.length, total: songs.length })}</p>
      <ul className={styles.list} data-testid="track-list">
        {visible.map(({ song, index }) => (
          <TrackItem
            key={`${song.id}-${index}`}
            song={song}
            index={index}
            isActive={index === currentIndex}
            canMoveUp={index > 0}
            canMoveDown={index < songs.length - 1}
            onPlay={() => onPlay(index)}
            onRemove={() => onRemove(index)}
            onMove={(delta) => onMove(index, delta)}
          />
        ))}
      </ul>
    </section>
  );
}
