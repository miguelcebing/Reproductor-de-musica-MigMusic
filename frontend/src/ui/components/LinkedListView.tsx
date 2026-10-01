/** Didactic view of the list: `head ⇄ node ⇄ … ⇄ node ⇄ tail` (`UX-002`). */

import { memo } from "react";

import type { Song } from "../../domain/types";
import { useT } from "../../i18n/useT";
import styles from "./Queue.module.css";

export interface LinkedListViewProps {
  readonly songs: readonly Song[];
  readonly currentIndex: number | null;
}

export const LinkedListView = memo(function LinkedListView({
  songs,
  currentIndex,
}: LinkedListViewProps): React.JSX.Element {
  const t = useT();

  return (
    <div className={styles.nodesPanel} data-testid="linked-list-view">
      <span className={styles.nodeHead}>{t("nodes.head")}</span>
      {songs.length === 0 && <span className={styles.node}>{t("nodes.empty")}</span>}
      {songs.map((song, index) => (
        <span key={`${song.id}-${index}`} className={styles.nodeArrow} aria-hidden="true">
          ⇄
          <span
            className={`${styles.node} ${index === currentIndex ? styles.nodeCurrent : ""}`}
            data-current={index === currentIndex}
            title={index === currentIndex ? t("nodes.current") : undefined}
          >
            {song.title}
          </span>
        </span>
      ))}
      <span className={styles.nodeArrow} aria-hidden="true">
        ⇄
      </span>
      <span className={styles.nodeTail}>{t("nodes.tail")}</span>
    </div>
  );
});
