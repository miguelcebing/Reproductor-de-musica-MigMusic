/** Stable per-browser device id: the scope key for local playlists.

 * The backend only narrows what a caller *sees* (`X-Device-Id` on playlist
 * list/create); it is UX isolation between devices, never authentication.
 */

const STORAGE_KEY = "mig_device_id";

function randomId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `d-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * This browser's device id, persisted in `localStorage`, or `null` when there
 * is no usable storage (unit tests, private-mode failures): callers then send
 * no header and the API answers with the unscoped view.
 */
export function getDeviceId(): string | null {
  try {
    if (typeof localStorage === "undefined") return null;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && stored.trim()) return stored.trim();
    const fresh = randomId();
    localStorage.setItem(STORAGE_KEY, fresh);
    return fresh;
  } catch {
    return null;
  }
}
