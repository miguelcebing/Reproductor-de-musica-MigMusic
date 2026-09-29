/** Time helpers shared by the player and the track list. */

/** Render seconds as `m:ss` (or `h:mm:ss` beyond an hour). */
export function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const total = Math.floor(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  const pad = (value: number): string => String(value).padStart(2, "0");
  return hours > 0 ? `${hours}:${pad(minutes)}:${pad(secs)}` : `${minutes}:${pad(secs)}`;
}

/** Clamp a ratio (0..1) into the 0..duration range. */
export function ratioToPosition(ratio: number, duration: number): number {
  const bounded = Math.min(1, Math.max(0, ratio));
  if (!Number.isFinite(duration) || duration <= 0) return 0;
  return bounded * duration;
}
