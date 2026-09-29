/** Interactive progress bar: click, drag and keyboard (`PLAYER-007`). */

import { useRef, useState } from "react";

import styles from "./Player.module.css";
import { formatTime, ratioToPosition } from "../utils/format";

export interface ProgressBarProps {
  readonly position: number;
  readonly duration: number;
  readonly disabled?: boolean;
  /** Seconds moved by a keyboard press (the `PLAYER-001` step). */
  readonly step: number;
  readonly label: string;
  readonly onSeek: (position: number) => void;
}

export function ProgressBar({
  position,
  duration,
  disabled = false,
  step,
  label,
  onSeek,
}: ProgressBarProps): React.JSX.Element {
  const trackRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);
  const [draggingPosition, setDraggingPosition] = useState<number | null>(null);

  const current = draggingPosition ?? position;
  const ratio = duration > 0 ? Math.min(1, Math.max(0, current / duration)) : 0;

  const positionFromClientX = (clientX: number): number => {
    const rect = trackRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return 0;
    return ratioToPosition((clientX - rect.left) / rect.width, duration);
  };

  const seekTo = (clientX: number): void => {
    if (disabled || duration <= 0) return;
    const target = positionFromClientX(clientX);
    setDraggingPosition(target);
    onSeek(target);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>): void => {
    if (disabled) return;
    const target =
      event.key === "ArrowRight"
        ? Math.min(duration, position + step)
        : event.key === "ArrowLeft"
          ? Math.max(0, position - step)
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? duration
              : null;
    if (target === null) return;
    event.preventDefault();
    setDraggingPosition(null);
    onSeek(target);
  };

  return (
    <div className={styles.progress}>
      <div
        ref={trackRef}
        className={styles.progressTrack}
        role="slider"
        tabIndex={disabled ? -1 : 0}
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={Math.round(duration)}
        aria-valuenow={Math.round(current)}
        aria-valuetext={formatTime(current)}
        aria-disabled={disabled}
        data-testid="progress-track"
        onKeyDown={handleKeyDown}
        onPointerDown={(event) => {
          if (disabled) return;
          draggingRef.current = true;
          event.currentTarget.setPointerCapture(event.pointerId);
          seekTo(event.clientX);
        }}
        onPointerMove={(event) => {
          if (!draggingRef.current) return;
          setDraggingPosition(positionFromClientX(event.clientX));
        }}
        onPointerUp={(event) => {
          if (!draggingRef.current) return;
          draggingRef.current = false;
          event.currentTarget.releasePointerCapture(event.pointerId);
          setDraggingPosition(null);
          onSeek(positionFromClientX(event.clientX));
        }}
        onPointerCancel={() => {
          draggingRef.current = false;
          setDraggingPosition(null);
        }}
      >
        <div className={styles.progressFill} style={{ width: `${ratio * 100}%` }} />
        <div className={styles.progressKnob} style={{ left: `${ratio * 100}%` }} />
      </div>
      <div className={styles.progressTimes}>
        <span>{formatTime(current)}</span>
        <span>{formatTime(duration)}</span>
      </div>
    </div>
  );
}
