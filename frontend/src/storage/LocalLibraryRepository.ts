/** IndexedDB persistence for local file metadata (`LOCAL-004`, `LOCAL-006`). */

import { get, set, del, keys } from "idb-keyval";

export interface LocalTrackMetadata {
  readonly id: string;
  readonly fileName: string;
  readonly fileHandle?: FileSystemFileHandle;
  /** Audio bytes. Absent on records written before blob persistence: those
   * tracks cannot be restored after a reload and are re-linked by the user. */
  readonly blob?: Blob;
  /** Embedded cover bytes, so the artwork URL can be rebuilt after a reload. */
  readonly artworkBlob?: Blob | null;
  readonly title: string;
  readonly artist: string;
  readonly album?: string | null;
  readonly duration: number;
  readonly artwork_url?: string | null;
  readonly external_url?: string | null;
  readonly lastModified: number;
  readonly size: number;
  readonly createdAt: number;
  readonly available: boolean;
}

const STORE_PREFIX = "migmusic:track:";

function key(id: string): string {
  return `${STORE_PREFIX}${id}`;
}

export class LocalLibraryRepository {
  async get(id: string): Promise<LocalTrackMetadata | undefined> {
    return get(key(id));
  }

  async getAll(): Promise<readonly LocalTrackMetadata[]> {
    const allKeys = await keys();
    const trackKeys = allKeys.filter(
      (k): k is string => typeof k === "string" && k.startsWith(STORE_PREFIX),
    );
    // One unreadable record (older schema, corrupted row) must not hide every
    // other track: read them independently and keep what survives.
    const settled = await Promise.allSettled(trackKeys.map((k) => get(k)));
    return settled.flatMap((result) =>
      result.status === "fulfilled" && result.value ? [result.value as LocalTrackMetadata] : [],
    );
  }

  async getBlob(id: string): Promise<Blob | undefined> {
    const track = await get(key(id));
    return track?.blob;
  }

  async put(track: LocalTrackMetadata): Promise<void> {
    await set(key(track.id), { ...track, available: true });
  }

  /** Re-attach the audio file of an existing track after the user picks it again. */
  async relink(id: string, file: File): Promise<LocalTrackMetadata | undefined> {
    const existing = await this.get(id);
    if (!existing) return undefined;
    const updated: LocalTrackMetadata = {
      ...existing,
      blob: file,
      fileName: file.name,
      lastModified: file.lastModified,
      size: file.size,
      available: true,
    };
    await this.put(updated);
    return updated;
  }

  async markUnavailable(id: string): Promise<void> {
    const existing = await this.get(id);
    if (existing) {
      await set(key(id), { ...existing, available: false });
    }
  }

  async remove(id: string): Promise<void> {
    await del(key(id));
  }

  async clear(): Promise<void> {
    const allKeys = await keys();
    const trackKeys = allKeys.filter(
      (k): k is string => typeof k === "string" && k.startsWith(STORE_PREFIX),
    );
    await Promise.all(trackKeys.map((k) => del(k)));
  }
}

export const localLibrary = new LocalLibraryRepository();
