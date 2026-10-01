/** Turning picked files into local tracks with metadata and object URLs (`LOCAL-003`). */

import type { SongInput } from "../domain/types";
import { localArtworkUrls, localFileUrls } from "./localFileUrls";
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
  const { extractMetadata, artworkBlobOf } = await import("./metadata");
  const metadata = await extractMetadata(file);
  const trackId = `local:${uuid()}`;

  // Create object URL for immediate playback
  const objectUrl = URL.createObjectURL(file);
  localFileUrls.set(trackId, objectUrl);

  // Artwork bytes are kept too: the object URL dies on reload, the Blob does not.
  const artworkBlob = artworkBlobOf(metadata.picture);
  const artworkUrl = artworkBlob ? URL.createObjectURL(artworkBlob) : null;
  if (artworkUrl) localArtworkUrls.set(trackId, artworkUrl);

  // Persist file blob in IndexedDB for recovery after reload
  const now = Date.now();
  await localLibrary.put({
    id: trackId,
    fileName: file.name,
    blob: file,
    artworkBlob,
    title: metadata.title,
    artist: metadata.artist,
    album: metadata.album ?? null,
    duration: Math.floor(metadata.duration) || 0,
    artwork_url: artworkUrl,
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
    artwork_url: artworkUrl,
    external_url: null,
    available: true,
  };
}

/**
 * Re-attach the file of a track whose bytes are gone (cleared site data, or a
 * record written before blob persistence). Keeps the track id, so the queue
 * and its playlists stay untouched.
 */
export async function relinkLocalTrack(trackId: string, file: File): Promise<boolean> {
  const updated = await localLibrary.relink(trackId, file);
  if (!updated) return false;
  revokeUrl(trackId);
  localFileUrls.set(trackId, URL.createObjectURL(file));
  return true;
}

function revokeUrl(trackId: string): void {
  const stale = localFileUrls.get(trackId);
  if (stale) URL.revokeObjectURL(stale);
  localFileUrls.delete(trackId);
}
