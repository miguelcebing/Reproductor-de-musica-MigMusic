/** Transport button: HeroUI `Button` plus the MigMusic spatial layer. */

import type { ReactNode } from "react";
import { Button } from "@heroui/react";

import styles from "./Player.module.css";

export interface IconButtonProps {
  readonly label: string;
  readonly onClick: () => void;
  readonly children: ReactNode;
  readonly disabled?: boolean;
  readonly active?: boolean;
  readonly primary?: boolean;
  /** Skip controls caption the arrow with `±N s`; glyph buttons leave it off. */
  readonly withLabel?: boolean;
  readonly testId?: string;
}

export function IconButton({
  label,
  onClick,
  children,
  disabled = false,
  active = false,
  primary = false,
  withLabel = false,
  testId,
}: IconButtonProps): React.JSX.Element {
  const classes = [styles.iconButton];
  if (primary) classes.push(styles.primary);
  if (active) classes.push(styles.iconButtonActive);

  /* Only shuffle/repeat are toggles; the rest must not claim a pressed state. */
  const toggleProps = active ? ({ "aria-pressed": true } as const) : {};

  return (
    <Button
      className={classes.join(" ")}
      type="button"
      aria-label={label}
      isDisabled={disabled}
      isIconOnly={!withLabel}
      size={primary ? "lg" : "md"}
      variant={primary ? "primary" : "ghost"}
      onPress={onClick}
      data-testid={testId}
      {...toggleProps}
    >
      {children}
    </Button>
  );
}
