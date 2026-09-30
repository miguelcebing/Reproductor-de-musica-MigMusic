/** In-memory store for local file object URLs (lost on reload, per LOCAL-006). */

import { localLibrary } from "../storage/LocalLibraryRepository";

export const localFileUrls = new Map<string, string>();

/** Create an object URL for a local file and store it by track ID. */
export function createObjectUrlForTrack(trackId: string, file: File): string {
  const url = URL.createObjectURL(file);
  localFileUrls.set(trackId, url);
  return url;
}

/** Retrieve the object URL for a track, or undefined if not in memory. */
export async function getObjectUrlForTrack(trackId: string): Promise<string | undefined> {
  // Check in-memory cache first
  const cached = localFileUrls.get(trackId);
  if (cached) return cached;

  // Try to restore from IndexedDB
  const blob = await localLibrary.getBlob(trackId);
  if (blob) {
    const url = URL.createObjectURL(blob);
    localFileUrls.set(trackId, url);
    return url;
  }

  return undefined;
}

/** Release the object URL for a track. */
export function revokeObjectUrlForTrack(trackId: string): void {
  const url = localFileUrls.get(trackId);
  if (url) {
    URL.revokeObjectURL(url);
    localFileUrls.delete(trackId);
  }
}

/** Clear all stored object URLs. */
export function clearAllObjectUrls(): void {
  for (const url of localFileUrls.values()) {
    URL.revokeObjectURL(url);
  }
  localFileUrls.clear();
}

/** Restore all object URLs from IndexedDB on app startup. */
export async function restoreObjectUrlsFromIndexedDB(): Promise<void> {
  const tracks = await localLibrary.getAll();
  for (const track of tracks) {
    if (track.blob && !localFileUrls.has(track.id)) {
      const url = URL.createObjectURL(track.blob);
      localFileUrls.set(track.id, url);
    }
  }
}