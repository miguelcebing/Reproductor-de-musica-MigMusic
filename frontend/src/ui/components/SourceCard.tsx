/** Bento tile summarising where the music comes from: local files and the
    optional Spotify link. Both rows reuse the existing controllers, so this
    is a second entry point, not a second source of truth. */

import { useT } from "../../i18n/useT";
import { PerspectiveGrid } from "../vengence/perspective-grid";
import styles from "./SourceCard.module.css";

export interface SourceCardProps {
  readonly trackCount: number;
  readonly spotifyConnected: boolean;
  readonly youtubeAvailable?: boolean;
  /** Open the add dialog focused on a given source tab. */
  readonly onAddFrom: (source: "local" | "spotify" | "youtube") => void;
  readonly onSpotifyConnect: () => void;
  readonly onSpotifyDisconnect: () => void;
}

export function SourceCard({
  trackCount,
  spotifyConnected,
  youtubeAvailable = false,
  onAddFrom,
  onSpotifyConnect,
  onSpotifyDisconnect,
}: SourceCardProps): React.JSX.Element {
  const t = useT();

  return (
    <div className={styles.source} data-testid="source-card">
      <div className={styles.scene} aria-hidden="true">
        <PerspectiveGrid gridSize={20} />
      </div>
      <h2 className={styles.title}>{t("source.title")}</h2>
      <ul className={styles.rows}>
        <li className={styles.row}>
          <span className={styles.dot} data-on="true" aria-hidden="true" />
          <span className={styles.labels}>
            <span className={styles.name}>{t("source.local")}</span>
            <span className={styles.meta}>{t("playlists.count", { count: trackCount })}</span>
          </span>
          <button
            type="button"
            className={styles.action}
            onClick={() => onAddFrom("local")}
            data-testid="source-add"
          >
            {t("dialog.addTitle")}
          </button>
        </li>
        <li className={styles.row}>
          <span className={styles.dot} data-on={String(spotifyConnected)} aria-hidden="true" />
          <span className={styles.labels}>
            <span className={styles.name}>{t("source.spotify")}</span>
            <span className={styles.meta}>
              {t(spotifyConnected ? "spotify.connected" : "spotify.disconnected")}
            </span>
          </span>
          <button
            type="button"
            className={styles.action}
            onClick={spotifyConnected ? onSpotifyDisconnect : onSpotifyConnect}
            data-testid="source-spotify"
          >
            {t(spotifyConnected ? "spotify.disconnect" : "spotify.connect")}
          </button>
        </li>
        <li className={styles.row}>
          <span className={styles.dot} data-on={String(youtubeAvailable)} aria-hidden="true" />
          <span className={styles.labels}>
            <span className={styles.name}>{t("source.youtube")}</span>
            <span className={styles.meta}>
              {t(youtubeAvailable ? "spotify.connected" : "youtube.notConfigured")}
            </span>
          </span>
          <button
            type="button"
            className={styles.action}
            onClick={() => onAddFrom("youtube")}
            data-testid="source-youtube"
          >
            {t("dialog.addTitle")}
          </button>
        </li>
      </ul>
    </div>
  );
}
