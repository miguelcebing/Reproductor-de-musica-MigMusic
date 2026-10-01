/** Accessible icon button used by every transport control. */

import type { ReactNode } from "react";
import { motion } from "framer-motion";

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
    <motion.button
      type="button"
      className={classes.join(" ")}
      aria-label={label}
      aria-pressed={active || undefined}
      disabled={disabled}
      onClick={onClick}
      data-testid={testId}
      whileHover={disabled ? {} : { scale: 1.08 }}
      whileTap={disabled ? {} : { scale: 0.94 }}
      transition={{ type: "spring", stiffness: 420, damping: 26 }}
    >
      {children}
    </motion.button>
  );
}
