/** Turning picked files into local tracks with metadata and object URLs (`LOCAL-003`). */

import type { SongInput } from "../domain/types";
import { localFileUrls } from "./localFileUrls";
import { localLibrary } from "../storage/LocalLibraryRepository";

function uuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Build the payload posted for one picked audio file, extracting metadata. */
export async function localSongFromFile(file: File): Promise<SongInput> {
  // `music-metadata` is heavy and only needed after the user picks files:
  // load it on demand so it stays out of the initial bundle (F9 perf).
  const { extractMetadata, artworkToObjectUrl } = await import("./metadata");
  const metadata = await extractMetadata(file);
  const trackId = `local:${uuid()}`;

  // Create object URL for immediate playback
  const objectUrl = URL.createObjectURL(file);
  localFileUrls.set(trackId, objectUrl);

  // Persist file blob in IndexedDB for recovery after reload
  const now = Date.now();
  await localLibrary.put({
    id: trackId,
    fileName: file.name,
    blob: file,
    title: metadata.title,
    artist: metadata.artist,
    album: metadata.album ?? null,
    duration: Math.floor(metadata.duration) || 0,
    artwork_url: metadata.picture ? artworkToObjectUrl(metadata.picture) : null,
    external_url: null,
    lastModified: file.lastModified,
    size: file.size,
    createdAt: now,
    available: true,
  });

  return {
    id: trackId,
    title: metadata.title,
    artist: metadata.artist,
    source: "local",
    duration: Math.floor(metadata.duration) || 0,
    album: metadata.album ?? null,
    artwork_url: metadata.picture ? artworkToObjectUrl(metadata.picture) : null,
    external_url: null,
    available: true,
  };
}

/** Revoke all object URLs for a list of files (cleanup on error). */
export function revokeObjectUrlsForFiles(files: File[]): void {
  for (const file of files) {
    const trackId = Array.from(localFileUrls.entries()).find(
      ([, url]) => url === URL.createObjectURL(file),
    )?.[0];
    if (trackId) {
      localFileUrls.delete(trackId);
      localLibrary.remove(trackId);
    }
  }
}