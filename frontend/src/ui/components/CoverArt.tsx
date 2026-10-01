/** Cover art with the subtle motion approved in `VIS-009`/`VIS-010`. */

import { memo } from "react";

import styles from "./Player.module.css";

export interface CoverArtProps {
  readonly artworkUrl: string | null;
  readonly alt: string;
  readonly playing: boolean;
}

export const CoverArt = memo(function CoverArt({
  artworkUrl,
  alt,
  playing,
}: CoverArtProps): React.JSX.Element {
  const classes = [styles.cover];
  if (playing) classes.push(styles.coverPlaying);

  return (
    <div className={classes.join(" ")} data-testid="cover-art">
      {artworkUrl ? (
        <img
          className={styles.coverImage}
          src={artworkUrl}
          alt={alt}
          width={260}
          height={260}
          loading="lazy"
          decoding="async"
          key={artworkUrl}
        />
      ) : (
        <>
          <span aria-hidden="true">♪</span>
          <span className={styles.discHole} aria-hidden="true" />
        </>
      )}
    </div>
  );
});
