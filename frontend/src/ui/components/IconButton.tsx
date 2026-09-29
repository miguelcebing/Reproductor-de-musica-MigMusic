/** Accessible icon button used by every transport control. */

import type { ReactNode } from "react";

import styles from "./Player.module.css";

export interface IconButtonProps {
  readonly label: string;
  readonly onClick: () => void;
  readonly children: ReactNode;
  readonly disabled?: boolean;
  readonly active?: boolean;
  readonly primary?: boolean;
  readonly testId?: string;
}

export function IconButton({
  label,
  onClick,
  children,
  disabled = false,
  active = false,
  primary = false,
  testId,
}: IconButtonProps): React.JSX.Element {
  const classes = [styles.iconButton];
  if (primary) classes.push(styles.primary);
  if (active) classes.push(styles.iconButtonActive);

  return (
    <button
      type="button"
      className={classes.join(" ")}
      aria-label={label}
      aria-pressed={active || undefined}
      disabled={disabled}
      onClick={onClick}
      data-testid={testId}
    >
      {children}
    </button>
  );
}
