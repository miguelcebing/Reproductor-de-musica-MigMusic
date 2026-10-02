/** Vengeance UI `perspective-grid`: a tilted floor of tiles that fades out at
    the edges. Vendored from the public registry and adapted to this app:
    `"use client"` (Next-only) is gone, `cn` points at our util and the tile
    count defaults to 20x20 so a small bento cell does not pay for 1600 nodes.
    Callers pass `bg-transparent dark:bg-transparent` when the grid has to sit
    on top of glass instead of an opaque surface. */

import { useEffect, useMemo, useState } from "react";

import { cn } from "../utils/cn";

export interface PerspectiveGridProps {
  /** Additional CSS classes for the grid container */
  className?: string;
  /** Number of tiles per row/column (default: 20) */
  gridSize?: number;
  /** Whether to show the gradient overlay (default: true) */
  showOverlay?: boolean;
  /** Fade radius percentage for the gradient overlay (default: 80) */
  fadeRadius?: number;
}

export function PerspectiveGrid({
  className,
  gridSize = 20,
  showOverlay = true,
  fadeRadius = 80,
}: PerspectiveGridProps): React.JSX.Element {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Memoize tiles array to prevent unnecessary re-renders
  const tiles = useMemo(() => Array.from({ length: gridSize * gridSize }), [gridSize]);

  return (
    <div
      className={cn(
        "relative h-full w-full overflow-hidden bg-transparent",
        "[--fade-stop:#ffffff] dark:[--fade-stop:#000000]",
        className,
      )}
      style={{
        perspective: "2000px",
        transformStyle: "preserve-3d",
      }}
    >
      <div
        className="absolute grid aspect-square w-[80rem] origin-center"
        style={{
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%) rotateX(30deg) rotateY(-5deg) rotateZ(20deg) scale(2)",
          transformStyle: "preserve-3d",
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          gridTemplateRows: `repeat(${gridSize}, 1fr)`,
        }}
      >
        {/* Tiles */}
        {mounted &&
          tiles.map((_, i) => (
            <div
              key={i}
              className="min-h-[1px] min-w-[1px] border border-gray-300 bg-transparent transition-colors duration-[1500ms] hover:duration-0 dark:border-gray-700"
            />
          ))}
      </div>

      {/* Radial Gradient Mask (Overlay) */}
      {showOverlay && (
        <div
          className="pointer-events-none absolute inset-0 z-10"
          style={{
            background: `radial-gradient(circle, transparent 25%, var(--fade-stop) ${fadeRadius}%)`,
          }}
        />
      )}
    </div>
  );
}

export default PerspectiveGrid;
