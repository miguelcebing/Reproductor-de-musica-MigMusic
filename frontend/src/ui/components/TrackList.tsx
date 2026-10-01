/** The queue: loading, empty and populated states (`UX-004`, `TEST-002`).

 * Live filtering, favorites-only toggle, Enter-to-find (`FEAT-001-c`) and
 * native drag & drop reordering (`FEAT-001-e`).
 */

import { memo, useCallback, useMemo, useState, type DragEvent } from "react";
import { AnimatePresence } from "framer-motion";

import type { Song } from "../../domain/types";
import { useT } from "../../i18n/useT";
import { EmptyState } from "./EmptyState";
import { TrackItem } from "./TrackItem";
import styles from "./Queue.module.css";
import { HeartIcon, PlusIcon } from "./icons";

export interface TrackListProps {
  readonly songs: readonly Song[];
  readonly currentIndex: number | null;
  readonly loading: boolean;
  readonly onPlay: (index: number) => void;
  readonly onRemove: (index: number) => void;
  readonly onMove: (index: number, delta: -1 | 1) => void;
  readonly onFavorite: (index: number, favorite: boolean) => void;
  readonly onReorder: (fromIndex: number, toIndex: number) => void;
  /** Resolves the first match for `text`, or `null` when nothing matches. */
  readonly onFind: (text: string) => Promise<number | null>;
  /** Called when the user wants to add music from the empty state. */
  readonly onAddMusic?: () => void;
}

export const TrackList = memo(function TrackList({
  songs,
  currentIndex,
  loading,
  onPlay,
  onRemove,
  onMove,
  onFavorite,
  onReorder,
  onFind,
  onAddMusic,
}: TrackListProps): React.JSX.Element {
  const t = useT();
  const [query, setQuery] = useState("");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [matchIndex, setMatchIndex] = useState<number | null>(null);
  const [noMatch, setNoMatch] = useState(false);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const handleDragStart = useCallback(
    (index: number, event: DragEvent<HTMLLIElement>) => {
      setDragIndex(index);
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", String(index));
    },
    [],
  );

  const handleDragOver = useCallback(
    (index: number, event: DragEvent<HTMLLIElement>) => {
      if (dragIndex === null) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      setDragOverIndex(index);
    },
    [dragIndex],
  );

  const handleDrop = useCallback(
    (index: number, event: DragEvent<HTMLLIElement>) => {
      event.preventDefault();
      const fallback = Number(event.dataTransfer.getData("text/plain"));
      const from = dragIndex ?? (Number.isNaN(fallback) ? null : fallback);
      setDragIndex(null);
      setDragOverIndex(null);
      if (from === null || from === index) return;
      onReorder(from, index);
    },
    [dragIndex, onReorder],
  );

  const handleDragEnd = useCallback((): void => {
    setDragIndex(null);
    setDragOverIndex(null);
  }, []);

  const handleDragLeave = useCallback((): void => {
    setDragOverIndex(null);
  }, []);

  // One shared object (identity moves only while a drag is running) so the
  // memoised rows skip re-renders for search, filters and hover changes.
  const drag = useMemo(
    () => ({
      onDragStart: handleDragStart,
      onDragOver: handleDragOver,
      onDrop: handleDrop,
      onDragEnd: handleDragEnd,
      onDragLeave: handleDragLeave,
    }),
    [handleDragStart, handleDragOver, handleDrop, handleDragEnd, handleDragLeave],
  );

  if (loading) {
    return <p className={styles.loading}>{t("list.loading")}</p>;
  }

  const normalized = query.trim().toLowerCase();
  let visible = songs.map((song, index) => ({ song, index }));
  if (normalized) {
    visible = visible.filter(
      ({ song }) =>
        song.title.toLowerCase().includes(normalized) ||
        song.artist.toLowerCase().includes(normalized),
    );
  }
  if (favoritesOnly) {
    visible = visible.filter(({ song }) => song.favorite);
  }

  if (songs.length === 0) {
    return (
      <EmptyState
        title={t("list.emptyTitle")}
        body={t("list.emptyBody")}
        {...(onAddMusic
          ? {
              action: {
                label: t("dialog.addTitle"),
                onClick: onAddMusic,
                icon: <PlusIcon width={14} height={14} />,
              },
            }
          : {})}
      />
    );
  }

  const handleSearchChange = (value: string): void => {
    setQuery(value);
    setMatchIndex(null);
    setNoMatch(false);
  };

  // Enter asks the API for the first match; the live filter keeps narrowing.
  const handleFind = async (): Promise<void> => {
    const text = query.trim();
    setMatchIndex(null);
    setNoMatch(false);
    if (text.length === 0) return;
    const found = await onFind(text);
    if (found === null) {
      setNoMatch(true);
      return;
    }
    setFavoritesOnly(false);
    setMatchIndex(found);
  };

  // Stable keys keep enter/exit animations on the rows that really changed;
  // a repeated song id falls back to the index to stay unique.
  const idCounts = new Map<string, number>();
  for (const song of songs) {
    idCounts.set(song.id, (idCounts.get(song.id) ?? 0) + 1);
  }
  const rowKey = (song: Song, index: number): string =>
    idCounts.get(song.id) === 1 ? song.id : `${song.id}#${index}`;

  return (
    <section aria-label={t("list.title")}>
      <div className={styles.searchRow}>
        <input
          className={`${styles.input} ${styles.search}`}
          type="search"
          value={query}
          placeholder={t("list.search")}
          aria-label={t("list.search")}
          data-testid="track-search"
          onChange={(event) => handleSearchChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void handleFind();
            }
          }}
        />
        <button
          type="button"
          className={`${styles.filter} ${favoritesOnly ? styles.filterActive : ""}`}
          aria-pressed={favoritesOnly}
          onClick={() => setFavoritesOnly((value) => !value)}
          data-testid="favorites-toggle"
        >
          <HeartIcon width={14} height={14} />
          {t("list.favoritesOnly")}
        </button>
      </div>
      <p className={styles.count}>{t("list.results", { shown: visible.length, total: songs.length })}</p>
      {noMatch && (
        <p className={styles.noMatch} role="status">
          {t("list.noMatch", { text: query.trim() })}
        </p>
      )}
      <ul className={styles.list} data-testid="track-list">
        <AnimatePresence initial={false}>
          {visible.map(({ song, index }) => (
            <TrackItem
              key={rowKey(song, index)}
              song={song}
              index={index}
              isActive={index === currentIndex}
              isMatch={index === matchIndex}
              isDragging={index === dragIndex}
              isDragOver={index === dragOverIndex && index !== dragIndex}
              canMoveUp={index > 0}
              canMoveDown={index < songs.length - 1}
              onPlay={onPlay}
              onRemove={onRemove}
              onMove={onMove}
              onFavorite={onFavorite}
              drag={drag}
            />
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
});
