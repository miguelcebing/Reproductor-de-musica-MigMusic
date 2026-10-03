/** Stable per-browser device id: the scope key for local playlists.

 * The backend requires `X-Device-Id` on every playlist and playback call and
 * scopes all data to it. The id is persisted in `localStorage` so it survives
 * reloads; when storage is unavailable (private mode, tests) an ephemeral id
 * is minted in memory for the life of the page, so a header is always sent.
 * This is UX isolation between devices, never authentication.
 */

const STORAGE_KEY = "mig_device_id";

/** Ephemeral fallback so callers always get a non-null id within one page. */
let ephemeralId: string | null = null;

function randomId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `d-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * This browser's device id, persisted in `localStorage`. When storage is
 * missing or throws, an in-memory id keeps the app working for this session.
 */
export function getDeviceId(): string {
  try {
    if (typeof localStorage !== "undefined") {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && stored.trim()) return stored.trim();
      const fresh = randomId();
      localStorage.setItem(STORAGE_KEY, fresh);
      return fresh;
    }
  } catch {
    // Storage is denied: fall through to the ephemeral id.
  }
  if (ephemeralId === null) ephemeralId = randomId();
  return ephemeralId;
}
