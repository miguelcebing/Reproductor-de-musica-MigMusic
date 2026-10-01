/** Current track announcement (`aria-live` for screen readers). */

import { memo } from "react";

import styles from "./Player.module.css";

export interface NowPlayingProps {
  readonly title: string;
  readonly artist: string;
}

export const NowPlaying = memo(function NowPlaying({
  title,
  artist,
}: NowPlayingProps): React.JSX.Element {
  return (
    <div className={styles.nowPlaying} aria-live="polite">
      <h2 className={styles.trackTitle} data-testid="now-playing-title">
        {title}
      </h2>
      <p className={styles.trackArtist}>{artist}</p>
    </div>
  );
});
