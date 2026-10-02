/** Illustrated empty states (`UX-004`). */

import { Button } from "@heroui/react";

import styles from "./Feedback.module.css";

export interface EmptyStateProps {
  readonly title: string;
  readonly body: string;
  /** Optional action button. */
  readonly action?: {
    readonly label: string;
    readonly onClick: () => void;
    /** Optional icon to show in the button. */
    readonly icon?: React.JSX.Element;
  };
}

export function EmptyState({ title, body, action }: EmptyStateProps): React.JSX.Element {
  return (
    <div className={styles.empty} data-testid="empty-state">
      <span className={styles.disc} aria-hidden="true">
        ♪
      </span>
      <p className={styles.emptyTitle}>{title}</p>
      <p className={styles.emptyBody}>{body}</p>
      {action && (
        <Button
          variant="primary"
          className={styles.emptyAction}
          onPress={action.onClick}
          data-testid="empty-action"
        >
          {action.icon}
          {action.label}
        </Button>
      )}
    </div>
  );
}
