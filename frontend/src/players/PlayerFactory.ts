/** Factory to create the right player for a source (`local-audio` skill). */

import type { AudioPlayer } from "./AudioPlayer";
import { LocalAudioPlayer } from "./LocalAudioPlayer";

export function createPlayerForSource(source: "local" | "spotify"): AudioPlayer {
  switch (source) {
    case "local":
      return new LocalAudioPlayer();
    case "spotify":
      // SpotifyPlayer will be implemented in F6
      throw new Error("Spotify player not implemented yet (F6)");
    default:
      throw new Error(`Unknown source: ${source}`);
  }
}