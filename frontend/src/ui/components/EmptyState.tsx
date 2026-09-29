/** Illustrated empty states (`UX-004`). */

import styles from "./Feedback.module.css";

export interface EmptyStateProps {
  readonly title: string;
  readonly body: string;
}

export function EmptyState({ title, body }: EmptyStateProps): React.JSX.Element {
  return (
    <div className={styles.empty} data-testid="empty-state">
      <span className={styles.disc} aria-hidden="true">
        ♪
      </span>
      <p className={styles.emptyTitle}>{title}</p>
      <p className={styles.emptyBody}>{body}</p>
    </div>
  );
}
