/** In-browser metadata extraction (`LOCAL-003`, `LOCAL-003a`). */

import * as mm from "music-metadata";

export interface ExtractedMetadata {
  readonly title: string;
  readonly artist: string;
  readonly album?: string | null;
  readonly duration: number;
  readonly picture?: { data: Uint8Array; format: string } | null;
}

/** Extract tags from a File/Blob using music-metadata. */
export async function extractMetadata(file: File): Promise<ExtractedMetadata> {
  try {
    const metadata = await mm.parseBlob(file, { duration: true, skipCovers: false });
    const common = metadata.common;
    const picture = metadata.common.picture?.[0];

    return {
      title: common.title?.trim() || file.name.replace(/\.[^.]+$/, "").trim() || "Track",
      artist: common.artist?.trim() || "",
      album: common.album?.trim() ?? null,
      duration: metadata.format.duration ?? 0,
      picture: picture
        ? { data: new Uint8Array(picture.data.buffer), format: picture.format }
        : null,
    };
  } catch {
    // Fallback if parsing fails
    return {
      title: file.name.replace(/\.[^.]+$/, "").trim() || "Track",
      artist: "",
      album: null,
      duration: 0,
      picture: null,
    };
  }
}

/** Embedded cover as a Blob, so the artwork URL can be rebuilt after a reload. */
export function artworkBlobOf(
  picture: { data: Uint8Array; format: string } | null | undefined,
): Blob | null {
  if (!picture) return null;
  try {
    return new Blob([picture.data], { type: picture.format });
  } catch {
    return null;
  }
}

/** Create an object URL for the embedded artwork, or return null. */
export function artworkToObjectUrl(
  picture: { data: Uint8Array; format: string } | null | undefined,
): string | null {
  const blob = artworkBlobOf(picture);
  return blob ? URL.createObjectURL(blob) : null;
}