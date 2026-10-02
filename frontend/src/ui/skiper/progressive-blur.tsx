/** Skiper UI `skiper41` — Progressive Blur.
    Vendored from the public registry (https://skiper-ui.com) and adapted to
    this app: the unused React default import is gone, the computed style key
    is typed explicitly and the node is marked decorative. It paints a masked
    backdrop blur, so it has to sit *behind* whatever it decorates. */

import type { CSSProperties } from "react";

export interface ProgressiveBlurProps {
  className?: string;
  backgroundColor?: string;
  position?: "top" | "bottom";
  height?: string;
  blurAmount?: string;
}

export function ProgressiveBlur({
  className = "",
  backgroundColor = "#f5f4f3",
  position = "top",
  height = "150px",
  blurAmount = "4px",
}: ProgressiveBlurProps): React.JSX.Element {
  const isTop = position === "top";

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute left-0 w-full select-none ${className}`}
      style={
        {
          ...(isTop ? { top: 0 } : { bottom: 0 }),
          height,
          background: isTop
            ? `linear-gradient(to top, transparent, ${backgroundColor})`
            : `linear-gradient(to bottom, transparent, ${backgroundColor})`,
          maskImage: isTop
            ? `linear-gradient(to bottom, ${backgroundColor} 50%, transparent)`
            : `linear-gradient(to top, ${backgroundColor} 50%, transparent)`,
          WebkitBackdropFilter: `blur(${blurAmount})`,
          backdropFilter: `blur(${blurAmount})`,
          WebkitUserSelect: "none",
          userSelect: "none",
        } as CSSProperties
      }
    />
  );
}

export default ProgressiveBlur;

/**
 * Skiper 41 Canvas_Landing_004 — React + framer motion
 * Inspired by and adapted from https://devouringdetails.com/
 * We respect the original creators. This is an inspired rebuild with our own taste and does not claim any ownership.
 * These animations aren’t associated with the devouringdetails.com . They’re independent recreations meant to study interaction design
 *
 * License & Usage:
 * - Free to use and modify in both personal and commercial projects.
 * - Attribution to Skiper UI is required when using the free version.
 * - No attribution required with Skiper UI Pro.
 *
 * Feedback and contributions are welcome.
 *
 * Author: @gurvinder-singh02
 * Website: https://gxuri.me
 * Twitter: https://x.com/Gur__vi
 */
