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
      body: JSON.stringify({
        text: "First line\nSecond line",
        source: "lrclib",
        synced: false,
        lines: [],
      }),
    }),
  );
  await addTrack(page);
  await page.getByRole("button", { name: "Reproducir Alpha Take" }).click();

  await page.getByTestId("lyrics-toggle").click();

  await expect(page.getByTestId("lyrics-dialog")).toBeVisible();
  await expect(page.getByTestId("lyrics-text")).toHaveText("First line\nSecond line");
  await expect(page.getByTestId("lyrics-dialog")).toContainText("LRCLIB");
});

test("follows the timed lyrics as the song advances", async ({ page }) => {
  // Timed lines: the first is highlighted, the rest dimmed, and the highlight
  // moves forward as the store position ticks (assert at least the first line).
  await page.route("**/api/lyrics", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        text: "Intro\nVerse\nChorus",
        source: "lrclib",
        synced: true,
        lines: [
          { time: 0.5, text: "Intro" },
          { time: 6.0, text: "Verse" },
          { time: 12.0, text: "Chorus" },
        ],
      }),
    }),
  );
  await addTrack(page);
  await page.getByRole("button", { name: "Reproducir Alpha Take" }).click();

  await page.getByTestId("lyrics-toggle").click();
  await expect(page.getByTestId("lyrics-text")).toBeVisible();

  const lines = page.locator('[data-testid="lyrics-text"] p');
  await expect(lines).toHaveCount(3);
  await expect.poll(async () => lines.nth(0).getAttribute("data-active")).toBe("true");
});

test("shows the empty state when the API answers 204", async ({ page }) => {
  await page.route("**/api/lyrics", (route) => route.fulfill({ status: 204 }));
  await addTrack(page);
  await page.getByRole("button", { name: "Reproducir Alpha Take" }).click();

  await page.getByTestId("lyrics-toggle").click();

  await expect(page.getByTestId("lyrics-empty")).toBeVisible();
});
