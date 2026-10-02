/** Fixed decorative space backdrop: nebulae, a deterministic starfield and a
    theme-aware vignette. Purely presentational, so it never reaches the
    accessibility tree or the pointer. */

import styles from "./SpaceBackdrop.module.css";

interface Star {
  readonly left: number;
  readonly top: number;
  readonly size: number;
  readonly opacity: number;
  readonly duration: number;
  readonly delay: number;
}

/** Deterministic LCG so the sky is identical on every render and reload. */
function makeStars(count: number): readonly Star[] {
  let seed = 0x2f6e2b1;
  const next = (): number => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0xffffffff;
  };

  const stars: Star[] = [];
  for (let i = 0; i < count; i += 1) {
    const bright = next() > 0.9;
    stars.push({
      left: next() * 100,
      top: next() * 100,
      size: bright ? 2.5 : 1 + Math.round(next()) * 0.5,
      opacity: 0.25 + next() * 0.7,
      duration: 4 + next() * 5,
      delay: -next() * 8,
    });
  }
  return stars;
}

const STARS = makeStars(96);

export function SpaceBackdrop(): React.JSX.Element {
  return (
    <div className={styles.backdrop} aria-hidden="true" data-testid="space-backdrop">
      <span className={`${styles.nebula} ${styles.nebulaOne}`} />
      <span className={`${styles.nebula} ${styles.nebulaTwo}`} />
      <span className={`${styles.nebula} ${styles.nebulaThree}`} />
      <div className={styles.stars}>
        {STARS.map((star, index) => (
          <span
            key={`${star.left}:${star.top}:${index}`}
            className={styles.star}
            style={{
              left: `${star.left}%`,
              top: `${star.top}%`,
              width: `${star.size}px`,
              height: `${star.size}px`,
              opacity: star.opacity,
              animationDuration: `${star.duration}s`,
              animationDelay: `${star.delay}s`,
            }}
          />
        ))}
      </div>
      <div className={styles.vignette} />
    </div>
  );
}
