/** Keeps audio alive when the tab is hidden or the screen locks (`F12`).
 *
 * Browsers pause media when a page goes to the background or the OS suspends
 * it; when the page comes back the store still says "playing", so we ask the
 * controller to resume only if the live player stopped. A user pause is never
 * undone because it flips the store to `playing: false`.
 */

import type { PlaybackController } from "./PlaybackController";

export class PlaybackResilience {
  private readonly resume = (): void => {
    if (typeof document !== "undefined" && document.visibilityState === "visible") {
      void this.controller.resumeIfInterrupted();
    }
  };

  constructor(private readonly controller: PlaybackController) {}

  start(): void {
    if (typeof document === "undefined") return;
    document.addEventListener("visibilitychange", this.resume);
    // `pageshow` also fires when a page returns from the back/forward cache.
    window.addEventListener("pageshow", this.resume);
  }

  stop(): void {
    if (typeof document === "undefined") return;
    document.removeEventListener("visibilitychange", this.resume);
    window.removeEventListener("pageshow", this.resume);
  }
}
