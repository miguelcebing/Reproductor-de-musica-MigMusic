/** Object URLs for local files: in-memory, rebuilt from IndexedDB on reload.

 * A `blob:` URL only lives as long as the document, so every reload (F5) needs
 * the bytes again (`LOCAL-006`). `restoreObjectUrlsFromIndexedDB` rebuilds the
 * audio and artwork URLs up-front, and reports the tracks whose bytes are gone
 * so the UI can offer to re-link the file.
 */

import type { Playlist, Song } from "../domain/types";
import { localLibrary } from "../storage/LocalLibraryRepository";

export const localFileUrls = new Map<string, string>();
/** Fresh artwork URL per local track (the stored one is a dead `blob:` URL). */
export const localArtworkUrls = new Map<string, string>();

/** Outcome of a restore: how many tracks play again, which ones need re-linking. */
export interface RestoreReport {
  readonly restored: number;
  /** Track ids with no audio bytes on this device (legacy records, cleared data). */
  readonly missing: readonly string[];
}

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
  for (const url of localArtworkUrls.values()) {
    URL.revokeObjectURL(url);
  }
  localArtworkUrls.clear();
}

/** Restore audio and artwork object URLs from IndexedDB on app startup. */
export async function restoreObjectUrlsFromIndexedDB(): Promise<RestoreReport> {
  const tracks = await localLibrary.getAll();
  const missing: string[] = [];
  let restored = 0;

  for (const track of tracks) {
    if (track.blob) {
      if (!localFileUrls.has(track.id)) {
        localFileUrls.set(track.id, URL.createObjectURL(track.blob));
        restored += 1;
      }
    } else {
      missing.push(track.id);
    }

    if (track.artworkBlob && track.artwork_url?.startsWith("blob:")) {
      localArtworkUrls.set(track.id, URL.createObjectURL(track.artworkBlob));
    }
  }

  return { restored, missing };
}

/**
 * Replace a dead `blob:` artwork URL with the one rebuilt at startup.
 * Non-local artwork (http URLs) and live `blob:` URLs are returned untouched;
 * an artwork that cannot be rebuilt falls back to the placeholder (`null`).
 */
export function withLiveArtwork<T extends { readonly id: string; readonly artwork_url?: string | null }>(
  song: T,
): T {
  const stored = song.artwork_url ?? null;
  if (!stored || !stored.startsWith("blob:")) return song;
  const fresh = localArtworkUrls.get(song.id) ?? null;
  return fresh === stored ? song : { ...song, artwork_url: fresh };
}

/** Same, for every song of a playlist (applied when the queue is loaded). */
export function withLiveArtworkIn(playlist: Playlist): Playlist {
  if (!playlist.songs.some((song: Song) => song.artwork_url?.startsWith("blob:"))) return playlist;
  return { ...playlist, songs: playlist.songs.map((song) => withLiveArtwork(song)) };
}
