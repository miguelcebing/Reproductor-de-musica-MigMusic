/** IndexedDB persistence for local file metadata (`LOCAL-004`, `LOCAL-006`). */

import { get, set, del, keys } from "idb-keyval";

export interface LocalTrackMetadata {
  readonly id: string;
  readonly fileName: string;
  readonly fileHandle?: FileSystemFileHandle;
  readonly title: string;
  readonly artist: string;
  readonly album?: string;
  readonly duration: number;
  readonly artwork?: string;
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
    const trackKeys = allKeys.filter((k): k is string => typeof k === "string" && k.startsWith(STORE_PREFIX));
    const tracks = await Promise.all(trackKeys.map((k) => get(k)));
    return tracks.filter((t): t is LocalTrackMetadata => t !== undefined);
  }

  async put(track: LocalTrackMetadata): Promise<void> {
    await set(key(track.id), { ...track, available: true });
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
    const trackKeys = allKeys.filter((k): k is string => typeof k === "string" && k.startsWith(STORE_PREFIX));
    await Promise.all(trackKeys.map((k) => del(k)));
  }
}

export const localLibrary = new LocalLibraryRepository();