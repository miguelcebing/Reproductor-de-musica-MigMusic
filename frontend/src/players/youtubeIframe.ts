/** Loader for the official YouTube IFrame Player API (loaded once).

 * The API script is injected lazily and its global is reused across players.
 * Playback stays inside YouTube's own player, so no audio is downloaded or
 * extracted on our side.
 */

export interface YouTubePlayerVars {
  autoplay?: 0 | 1;
  controls?: 0 | 1;
  disablekb?: 0 | 1;
  modestbranding?: 0 | 1;
  playsinline?: 0 | 1;
  rel?: 0 | 1;
  origin?: string;
}

export interface YouTubeVideoData {
  readonly video_id: string;
  readonly title?: string;
  readonly author?: string;
}

export interface YouTubePlayerInstance {
  playVideo(): void;
  pauseVideo(): void;
  stopVideo(): void;
  loadVideoById(videoId: string, startSeconds?: number): void;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  setVolume(volume: number): void;
  mute(): void;
  unMute(): void;
  getCurrentTime(): number;
  getDuration(): number;
  getPlayerState(): number;
  destroy(): void;
}

export interface YouTubePlayerEvent {
  readonly target: YouTubePlayerInstance;
  readonly data?: number;
}

export interface YouTubePlayerOptions {
  readonly videoId: string;
  readonly playerVars?: YouTubePlayerVars;
  readonly events?: {
    readonly onReady?: (event: YouTubePlayerEvent) => void;
    readonly onStateChange?: (event: YouTubePlayerEvent) => void;
    readonly onError?: (event: YouTubePlayerEvent) => void;
  };
}

export interface YouTubeApi {
  Player: new (element: HTMLElement | string, options: YouTubePlayerOptions) => YouTubePlayerInstance;
  PlayerState: {
    readonly UNSTARTED: number;
    readonly ENDED: number;
    readonly PLAYING: number;
    readonly PAUSED: number;
    readonly BUFFERING: number;
    readonly CUED: number;
  };
}

declare global {
  interface Window {
    YT?: YouTubeApi;
    onYouTubeIframeAPIReady?: () => void;
  }
}

const SCRIPT_ID = "youtube-iframe-api";
let apiPromise: Promise<YouTubeApi> | null = null;

/** Resolve the global `YT` namespace, injecting the official script once. */
export function loadYouTubeApi(): Promise<YouTubeApi> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("YouTube API needs a browser"));
  }
  if (window.YT?.Player) return Promise.resolve(window.YT);
  if (apiPromise) return apiPromise;

  apiPromise = new Promise<YouTubeApi>((resolve, reject) => {
    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      previous?.();
      if (window.YT?.Player) resolve(window.YT);
      else reject(new Error("YouTube API did not expose YT.Player"));
    };

    if (document.getElementById(SCRIPT_ID)) return; // script loading already

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = "https://www.youtube.com/iframe_api";
    script.async = true;
    script.onerror = () => reject(new Error("Failed to load the YouTube IFrame API"));
    document.head.appendChild(script);
  });
  return apiPromise;
}
