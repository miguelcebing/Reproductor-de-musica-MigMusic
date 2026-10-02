/** Vengeance UI `border-beam`: a gradient light orbiting a card's border.
    Vendored from the public registry and adapted to this app:
    the `styled-jsx` block became `border-beam.css`, `cn` points at our util and
    the `!important` prefixes are dropped (nothing else sets those properties).
    Decorative only: it carries no text, is never focusable and never receives
    pointer input. */

import type { CSSProperties } from "react";

import { cn } from "../utils/cn";

import "./border-beam.css";

export interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  borderWidth?: number;
  anchor?: number;
  colorFrom?: string;
  colorTo?: string;
  delay?: number;
}

export function BorderBeam({
  className,
  size = 200,
  duration = 15,
  anchor = 90,
  borderWidth = 1.5,
  colorFrom = "#7c3aed",
  colorTo = "#a855f7",
  delay = 0,
}: BorderBeamProps): React.JSX.Element {
  return (
    <div
      aria-hidden="true"
      style={
        {
          "--size": size,
          "--duration": duration,
          "--anchor": anchor,
          "--border-width": borderWidth,
          "--color-from": colorFrom,
          "--color-to": colorTo,
          "--delay": delay,
        } as CSSProperties
      }
      className={cn(
        "mm-border-beam pointer-events-none absolute inset-[0] rounded-[inherit]",
        "after:absolute after:aspect-square after:content-[''] after:w-[calc(var(--size)*1px)]",
        "after:[animation:border-beam_calc(var(--duration)*1s)_infinite_linear] after:[animation-delay:var(--delay)s]",
        "after:[background:linear-gradient(to_left,var(--color-from),var(--color-to),transparent)]",
        "after:[offset-anchor:calc(var(--anchor)*1%)_50%] after:[offset-path:rect(0_auto_auto_0_round_calc(var(--size)*1px))]",
        className,
      )}
    />
  );
}

export default BorderBeam;
