/** Current track announcement (`aria-live`) plus the lyrics entry point (`F13`). */

import { memo } from "react";

import { useT } from "../../i18n/useT";
import styles from "./Player.module.css";

export interface NowPlayingProps {
  readonly title: string;
  readonly artist: string;
  /** Only show the lyrics button when a track is loaded. */
  readonly lyricsEnabled?: boolean;
  readonly lyricsOpen?: boolean;
  readonly onToggleLyrics?: () => void;
}

export const NowPlaying = memo(function NowPlaying({
  title,
  artist,
  lyricsEnabled = false,
  lyricsOpen = false,
  onToggleLyrics,
}: NowPlayingProps): React.JSX.Element {
  const t = useT();
  return (
    <div className={styles.nowPlaying} aria-live="polite">
      <div className={styles.titleRow}>
        <h2 className={styles.trackTitle} data-testid="now-playing-title">
          {title}
        </h2>
        {lyricsEnabled && onToggleLyrics && (
          <button
            type="button"
            className={`${styles.lyricsButton} ${lyricsOpen ? styles.lyricsButtonActive : ""}`}
            onClick={onToggleLyrics}
            aria-pressed={lyricsOpen}
            aria-label={t("lyrics.open")}
            title={t("lyrics.open")}
            data-testid="lyrics-toggle"
          >
            {t("lyrics.title")}
          </button>
        )}
      </div>
      <p className={styles.trackArtist}>{artist}</p>
    </div>
  );
});
