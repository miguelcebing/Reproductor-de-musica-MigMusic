/** LOCAL-006: local tracks (and their queue) survive an F5 reload.

 * The queue and the file bytes come back, but playback never resumes on its
 * own: the user presses play to continue after the reload.
 */

import { expect, test, type Page } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const TRACK = makeWav("Reload Anthem", 30);

function progressValue(page: Page): Promise<number> {
  return page
    .getByTestId("progress-track")
    .getAttribute("aria-valuenow")
    .then((value) => Number(value ?? 0));
}

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("local track added before the reload still plays after it", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await page.goto("/");
  await page.getByTestId("playlist-name").fill("F5 Mix");
  await page.getByTestId("playlist-create").click();

  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([TRACK]);
  await page.getByTestId("dialog-submit").click();
  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText("Reload Anthem");

  await page.getByRole("button", { name: "Reproducir Reload Anthem" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Reload Anthem");
  await expect
    .poll(() => progressValue(page), { timeout: 15_000 })
    .toBeGreaterThan(0);

  await page.reload();

  // The queue comes back from the backend and the file URL from IndexedDB, but
  // nothing plays until the user asks for it.
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText("Reload Anthem");
  await expect(page.getByTestId("relink-0")).toHaveCount(0);
  await expect(page.getByTestId("now-playing-title")).toHaveText("Nada en reproducción");

  // Pressing play uses the restored blob: no missing-file toast, and the
  // transport actually moves.
  await page.getByRole("button", { name: "Reproducir Reload Anthem" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Reload Anthem");
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Pausar");
  await expect
    .poll(() => progressValue(page), { timeout: 15_000 })
    .toBeGreaterThan(0);
  await expect(page.getByText("no está en este dispositivo")).toHaveCount(0);

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
