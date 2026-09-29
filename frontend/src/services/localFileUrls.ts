/** In-memory store for local file object URLs (lost on reload, per LOCAL-006). */

export const localFileUrls = new Map<string, string>();

/** Create an object URL for a local file and store it by track ID. */
export function createObjectUrlForTrack(trackId: string, file: File): string {
  const url = URL.createObjectURL(file);
  localFileUrls.set(trackId, url);
  return url;
}

/** Retrieve the object URL for a track, or undefined if not in memory. */
export function getObjectUrlForTrack(trackId: string): string | undefined {
  return localFileUrls.get(trackId);
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