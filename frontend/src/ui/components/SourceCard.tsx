/** Bento tile summarising where the music comes from: local files and the
    optional Spotify link. Both rows reuse the existing controllers, so this
    is a second entry point, not a second source of truth. */

import { useT } from "../../i18n/useT";
import { PerspectiveGrid } from "../vengence/perspective-grid";
import styles from "./SourceCard.module.css";

export interface SourceCardProps {
  readonly trackCount: number;
  readonly canAdd: boolean;
  readonly spotifyConnected: boolean;
  readonly onAddMusic: () => void;
  readonly onSpotifyConnect: () => void;
  readonly onSpotifyDisconnect: () => void;
}

export function SourceCard({
  trackCount,
  canAdd,
  spotifyConnected,
  onAddMusic,
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
            onClick={onAddMusic}
            disabled={!canAdd}
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
      </ul>
    </div>
  );
}
