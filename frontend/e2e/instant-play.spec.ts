/** Instant playback (`F12`): the click is answered before the network, and a
 * burst of clicks ends with only the last track playing.
 *
 * Local WAV tracks are used because they are deterministic in CI; the numbers
 * printed here are the honest dev-machine baseline for click → UI and
 * click → audible progress.
 */

import { expect, test } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const ALPHA = makeWav("Alpha Take", 20);
const BETA = makeWav("Beta Groove", 20);
const GAMMA = makeWav("Gamma Line", 20);

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("answers the click before the network and only the last pick plays", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("playlist-name").fill("Instant");
  await page.getByTestId("playlist-create").click();
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([ALPHA, BETA, GAMMA]);
  await page.getByTestId("dialog-submit").click();
  await expect(page.getByTestId("track-row")).toHaveCount(3);

  // --- UI reaction and audio start, measured inside the browser ------------
  // (Node-side timestamps would include Playwright's click actionability.)
  const timings = await page.evaluate(async () => {
    const row = document.querySelector('[data-testid="track-row"] button') as HTMLButtonElement;
    const title = document.querySelector('[data-testid="now-playing-title"]') as HTMLElement;
    const track = document.querySelector('[data-testid="progress-track"]') as HTMLElement;
    const waitFor = (
      predicate: () => boolean,
      target: Element,
      options: MutationObserverInit,
    ): Promise<void> =>
      new Promise((resolve) => {
        const observer = new MutationObserver(() => {
          if (predicate()) {
            observer.disconnect();
            resolve();
          }
        });
        observer.observe(target, options);
        if (predicate()) {
          observer.disconnect();
          resolve();
        }
      });

    const start = performance.now();
    row.click();
    await waitFor(() => title.textContent === "Alpha Take", title, {
      childList: true,
      characterData: true,
      subtree: true,
    });
    const uiMs = performance.now() - start;
    await waitFor(() => Number(track.getAttribute("aria-valuenow") ?? 0) > 0, track, {
      attributes: true,
      attributeFilter: ["aria-valuenow"],
    });
    return { uiMs, audioMs: performance.now() - start };
  });
  console.log(
    `[instant-play] click→title ${timings.uiMs.toFixed(1)} ms, click→audio ${timings.audioMs.toFixed(1)} ms`,
  );

  // The UI must answer well before a network round trip to a cold backend.
  expect(timings.uiMs).toBeLessThan(300);

  // --- A burst of picks: only the last one may play -------------------------
  await page.getByRole("button", { name: "Reproducir Beta Groove" }).click();
  await page.getByRole("button", { name: "Reproducir Gamma Line" }).click();

  await expect(page.getByTestId("now-playing-title")).toHaveText("Gamma Line");
  await expect
    .poll(async () => {
      const rows = page.locator('[data-testid="track-row"][data-active="true"]');
      return rows.count();
    })
    .toBe(1);
  await expect(page.locator('[data-testid="track-row"][data-active="true"]')).toHaveAttribute(
    "data-index",
    "2",
  );

  // The loading flag clears once every pick has settled.
  await expect
    .poll(async () => page.locator('[data-testid="track-row"][data-loading="true"]').count())
    .toBe(0);
});
