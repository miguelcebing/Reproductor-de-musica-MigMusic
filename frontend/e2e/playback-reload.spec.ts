/** After a reload the queue is restored but nothing plays until the user asks.

 * The playback context survives in the backend, but the app deliberately
 * starts with an empty player (`refresh(restorePlaying=false)`): a reload must
 * not reopen audio on its own. The playlist being played is still the one
 * shown, so the list on screen keeps matching the backend transport.
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

test("reload restores the queue but starts with an empty player", async ({ page }) => {
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

  await page.getByRole("button", { name: "Reproducir Beta Two" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Beta Two");

  await page.reload();

  // Nothing resumes by itself: the player is empty until the user presses play.
  await expect(page.getByTestId("now-playing-title")).toHaveText("Nada en reproducción");

  // The queue is restored, and the playlist shown is the one that was playing.
  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(0)).toContainText("Beta One");
  await expect(rows.nth(1)).toContainText("Beta Two");

  // Pressing play on the restored queue brings the track back.
  await page.getByRole("button", { name: "Reproducir Beta Two" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Beta Two");

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
