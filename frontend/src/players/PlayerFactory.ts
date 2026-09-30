/** Factory to create the right player for a source (`local-audio` skill).

 * `Song.source` picks the strategy (`SKILL3` hard rule): local files go to the
 * HTML5 player, Spotify URIs to the Web Playback SDK player. The SDK session
 * is shared across tracks so the device stays connected while the queue runs.
 */

import type { AudioPlayer } from "./AudioPlayer";
import { LocalAudioPlayer } from "./LocalAudioPlayer";
import { SpotifyPlayer, type SpotifyPlaybackControl } from "./SpotifyPlayer";
import { WebPlaybackSession, type SpotifySdkSession } from "./spotifySdk";
import type { ApiClient } from "../services/apiClient";

export interface PlayerFactoryOptions {
  /** Required for the Spotify source: token endpoint + play proxy. */
  readonly api?: ApiClient;
}

let shared: { api: ApiClient; session: SpotifySdkSession } | null = null;

export function createPlayerForSource(
  source: "local" | "spotify",
  options?: PlayerFactoryOptions,
): AudioPlayer {
  switch (source) {
    case "local":
      return new LocalAudioPlayer();
    case "spotify": {
      const api = options?.api;
      if (!api) throw new Error("SpotifyPlayer requires an ApiClient");
      return new SpotifyPlayer({ control: playbackControlFor(api), session: sessionFor(api) });
    }
    default:
      throw new Error(`Unknown source: ${source}`);
  }
}

/** Backend proxy used to queue a URI on the SDK device. */
export function playbackControlFor(api: ApiClient): SpotifyPlaybackControl {
  return {
    play: (uris, deviceId, positionMs) =>
      api.spotifyPlay({
        uris: [...uris],
        device_id: deviceId,
        position_ms: positionMs ?? 0,
      }),
  };
}

function sessionFor(api: ApiClient): SpotifySdkSession {
  if (!shared || shared.api !== api) {
    shared = {
      api,
      session: new WebPlaybackSession(() =>
        api.spotifyToken().then((token) => token.access_token),
      ),
    };
  }
  return shared.session;
}
