// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import { PlaybackResilience } from "./playbackResilience";
import type { PlaybackController } from "./PlaybackController";

function setVisibility(state: "visible" | "hidden"): void {
  Object.defineProperty(document, "visibilityState", { value: state, configurable: true });
}

function makeController() {
  return {
    resumeIfInterrupted: vi.fn().mockResolvedValue(undefined),
  } as unknown as PlaybackController;
}

afterEach(() => {
  setVisibility("visible");
});

describe("PlaybackResilience", () => {
  it("resumes audio when the page becomes visible again", () => {
    const controller = makeController();
    const resilience = new PlaybackResilience(controller);
    resilience.start();

    setVisibility("visible");
    document.dispatchEvent(new Event("visibilitychange"));

    expect(controller.resumeIfInterrupted).toHaveBeenCalledTimes(1);
    resilience.stop();
  });

  it("does not resume while the page stays hidden", () => {
    const controller = makeController();
    const resilience = new PlaybackResilience(controller);
    resilience.start();

    setVisibility("hidden");
    document.dispatchEvent(new Event("visibilitychange"));

    expect(controller.resumeIfInterrupted).not.toHaveBeenCalled();
    resilience.stop();
  });

  it("stops listening after stop()", () => {
    const controller = makeController();
    const resilience = new PlaybackResilience(controller);
    resilience.start();
    resilience.stop();

    setVisibility("visible");
    document.dispatchEvent(new Event("visibilitychange"));

    expect(controller.resumeIfInterrupted).not.toHaveBeenCalled();
  });
});
