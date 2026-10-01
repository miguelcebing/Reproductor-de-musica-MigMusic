/** Auto-advance mid-list and stop at the tail (repeat off never loops). */

import { expect, test } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const SHORT_ONE = makeWav("Short One", 1);
const SHORT_TWO = makeWav("Short Two", 1);

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("the next track starts on its own and the list stops at the tail", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await page.goto("/");

  // --- Two one-second tracks --------------------------------------------
  await page.getByTestId("playlist-name").fill("Auto Advance");
  await page.getByTestId("playlist-create").click();

  await page.getByTestId("add-music").click();
  await expect(page.getByTestId("add-dialog")).toBeVisible();
  await page.getByTestId("file-input").setInputFiles([SHORT_ONE, SHORT_TWO]);
  await page.getByTestId("dialog-submit").click();
  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(0)).toContainText("Short One");
  await expect(rows.nth(1)).toContainText("Short Two");

  // --- Play the first track ---------------------------------------------
  await page.getByRole("button", { name: "Reproducir Short One" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Short One");
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Pausar");

  // --- Mid-list auto-advance: no click, the second track takes over ------
  await expect(page.getByTestId("now-playing-title")).toHaveText("Short Two", {
    timeout: 20_000,
  });
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Pausar");

  // --- Tail with repeat off: playback stops, the song stays visible ------
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Reproducir", {
    timeout: 20_000,
  });
  await expect(page.getByTestId("now-playing-title")).toHaveText("Short Two");

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
