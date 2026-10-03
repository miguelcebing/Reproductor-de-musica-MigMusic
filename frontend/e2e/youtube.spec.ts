/** YouTube Music entry points (`F8`): quick buttons open the right tab.
 *
 * The search itself hits the unofficial YouTube Music API, so the assertions
 * stay on the UI wiring (buttons → dialog → tab) and do not depend on live
 * results.
 */

import { expect, test } from "@playwright/test";
import { resetBackend } from "./helpers";

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("the playlist bar exposes a YouTube button that opens the YouTube tab", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("add-youtube").click();

  await expect(page.getByTestId("add-dialog")).toBeVisible();
  await expect(page.getByTestId("youtube-query")).toBeVisible();
});

test("the source card jumps straight to the YouTube tab", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("source-youtube").click();

  await expect(page.getByTestId("add-dialog")).toBeVisible();
  await expect(page.getByTestId("youtube-query")).toBeVisible();
});

test("the source card's local button opens the local tab", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("source-add").click();

  await expect(page.getByTestId("file-input")).toBeVisible();
});
