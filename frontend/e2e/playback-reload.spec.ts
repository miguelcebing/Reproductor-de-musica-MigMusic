/** After a reload the visible playlist must be the one being played.

 * The playback context survives in the backend, but `activeId` restarts on
 * every load: showing the first playlist while another one plays made the
 * transport look broken (the highlight and the next/previous toasts did not
 * match the list on screen).
 */

import { expect, test } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const A_ONE = makeWav("Alpha One");
const A_TWO = makeWav("Alpha Two");
const B_ONE = makeWav("Beta One");
const B_TWO = makeWav("Beta Two");

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("reload keeps showing the playlist that is playing", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await page.goto("/");

  // Two playlists: Alpha first, Beta second (the one that will play).
  await page.getByTestId("playlist-name").fill("Alpha");
  await page.getByTestId("playlist-create").click();
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([A_ONE, A_TWO]);
  await page.getByTestId("dialog-submit").click();
  await expect(page.getByTestId("track-row")).toHaveCount(2);

  await page.getByTestId("playlist-name").fill("Beta");
  await page.getByTestId("playlist-create").click();
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([B_ONE, B_TWO]);
  await page.getByTestId("dialog-submit").click();
  await expect(page.getByTestId("track-row")).toHaveCount(2);

  // Play Beta's last song, so the edge toast is meaningful after the reload.
  await page.getByRole("button", { name: "Reproducir Beta Two" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Beta Two");

  await page.reload();

  // The app must resume on the playlist being played, not on the first one.
  await expect(page.getByTestId("now-playing-title")).toHaveText("Beta Two");
  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(0)).toContainText("Beta One");
  await expect(rows.nth(1)).toContainText("Beta Two");
  await expect(page.locator('[data-testid="track-row"][data-active="true"]')).toHaveCount(1);

  // The tail still answers with the edge toast (PLAYLIST-009 = A).
  await page.getByTestId("next").click();
  await expect(page.getByTestId("toasts")).toContainText("Estás en la última canción");
  await expect(page.getByTestId("now-playing-title")).toHaveText("Beta Two");

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
