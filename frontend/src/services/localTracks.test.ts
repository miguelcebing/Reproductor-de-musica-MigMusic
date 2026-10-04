import { describe, expect, it } from "vitest";

import { isSupportedAudioFile, MAX_LOCAL_FILE_BYTES } from "./localTracks";

function makeFile(name: string, type: string, size = 1024): File {
  const blob = new Blob([new Uint8Array(Math.min(size, 64))], { type });
  // Blob size is bounded by the payload; override `size` for the edge case.
  Object.defineProperty(blob, "size", { value: size });
  const file = new File([blob], name, { type });
  Object.defineProperty(file, "size", { value: size });
  return file;
}

describe("isSupportedAudioFile", () => {
  it("accepts MP3 and WAV by extension and mime", () => {
    expect(isSupportedAudioFile(makeFile("song.mp3", "audio/mpeg"))).toBe(true);
    expect(isSupportedAudioFile(makeFile("song.wav", "audio/wav"))).toBe(true);
  });

  it("accepts a file whose mime the browser left empty", () => {
    expect(isSupportedAudioFile(makeFile("song.MP3", ""))).toBe(true);
  });

  it("rejects other formats", () => {
    expect(isSupportedAudioFile(makeFile("clip.mp4", "video/mp4"))).toBe(false);
    expect(isSupportedAudioFile(makeFile("song.flac", "audio/flac"))).toBe(false);
  });

  it("rejects files over the size limit", () => {
    expect(isSupportedAudioFile(makeFile("huge.wav", "audio/wav", MAX_LOCAL_FILE_BYTES + 1))).toBe(
      false,
    );
  });
});
