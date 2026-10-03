import { expect, type APIRequestContext } from "@playwright/test";

export interface TestAudioFile {
  readonly name: string;
  readonly mimeType: string;
  readonly buffer: Buffer;
}

/**
 * Minimal 8-bit PCM mono WAV (12 s by default): Chromium plays it and
 * `music-metadata` derives the duration, so seek/skip have real bounds.
 */
export function makeWav(name: string, seconds = 12): TestAudioFile {
  const sampleRate = 8000;
  const samples = Math.floor(sampleRate * seconds);
  const buffer = Buffer.alloc(44 + samples);
  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + samples, 4);
  buffer.write("WAVE", 8);
  buffer.write("fmt ", 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20); // PCM
  buffer.writeUInt16LE(1, 22); // mono
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate, 28); // byte rate (8-bit mono)
  buffer.writeUInt16LE(1, 32); // block align
  buffer.writeUInt16LE(8, 34); // bits per sample
  buffer.write("data", 36);
  buffer.writeUInt32LE(samples, 40);
  for (let i = 0; i < samples; i += 1) {
    const value = Math.round(127 + 60 * Math.sin((2 * Math.PI * 440 * i) / sampleRate));
    buffer.writeUInt8(value, 44 + i);
  }
  return {
    name: name.endsWith(".wav") ? name : `${name}.wav`,
    mimeType: "audio/wav",
    buffer,
  };
}

/**
 * Wipe every playlist so each spec starts from a clean backend.
 *
 * Uses the development-only reset endpoint: `GET /api/playlists` now requires
 * a device header and would only ever return the caller's own playlists.
 * `APP_ENV=development` in the Playwright backend, so the route exists.
 */
export async function resetBackend(request: APIRequestContext): Promise<void> {
  const response = await request.post("/api/testing/reset");
  expect(response.ok(), "POST /api/testing/reset must answer 200").toBe(true);
}
