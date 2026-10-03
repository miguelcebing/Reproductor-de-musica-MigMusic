/** Lyrics panel (`F13`): the button opens the modal and it settles into a
 * loaded, empty or error state without breaking playback.
 *
 * The real backend would call YouTube/LRCLIB, so the network response is
 * stubbed here; the point is the UI contract, not the upstream content.
 */

import { expect, test, type Page } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const ALPHA = makeWav("Alpha Take", 20);

async function addTrack(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByTestId("playlist-name").fill("Lyrics");
  await page.getByTestId("playlist-create").click();
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([ALPHA]);
  await page.getByTestId("dialog-submit").click();
  await expect(page.getByTestId("track-row")).toHaveCount(1);
}

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("shows the lyrics returned by the API", async ({ page }) => {
  await page.route("**/api/lyrics", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ text: "First line\nSecond line", source: "lrclib", synced: false }),
    }),
  );
  await addTrack(page);
  await page.getByRole("button", { name: "Reproducir Alpha Take" }).click();

  await page.getByTestId("lyrics-toggle").click();

  await expect(page.getByTestId("lyrics-dialog")).toBeVisible();
  await expect(page.getByTestId("lyrics-text")).toHaveText("First line\nSecond line");
  await expect(page.getByTestId("lyrics-dialog")).toContainText("LRCLIB");
});

test("shows the empty state when the API answers 204", async ({ page }) => {
  await page.route("**/api/lyrics", (route) => route.fulfill({ status: 204 }));
  await addTrack(page);
  await page.getByRole("button", { name: "Reproducir Alpha Take" }).click();

  await page.getByTestId("lyrics-toggle").click();

  await expect(page.getByTestId("lyrics-empty")).toBeVisible();
});
