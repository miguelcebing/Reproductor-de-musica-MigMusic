/** Turning picked files into local tracks.

 * Metadata reading (ID3 tags, duration) lands in F5 (`LOCAL-003`); until then
 * the filename is the best title we have and the duration stays unknown (0).
 */

import type { SongInput } from "../domain/types";

function uuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Build the payload posted for one picked audio file. */
export function localSongFromFile(file: File): SongInput {
  const title = file.name.replace(/\.[^.]+$/, "").trim() || "Track";
  return {
    id: `local:${uuid()}`,
    title,
    artist: "",
    source: "local",
    duration: 0,
    available: true,
  };
}
