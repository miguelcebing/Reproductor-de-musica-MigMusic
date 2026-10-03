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

test("the add dialog exposes the YouTube Music tab", async ({ page }) => {
  await page.goto("/");

  // YouTube lives only inside the add dialog, not as a separate bar button.
  await expect(page.getByTestId("add-youtube")).toHaveCount(0);
  await page.getByTestId("add-music").click();
  await page.getByTestId("tab-youtube").click();

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

test("all three source tabs stay inside the dialog and are clickable", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("add-music").click();
  await expect(page.getByTestId("add-dialog")).toBeVisible();

  const dialogBox = await page.getByTestId("add-dialog").boundingBox();
  expect(dialogBox).not.toBeNull();

  for (const id of ["tab-local", "tab-spotify", "tab-youtube"]) {
    const tab = page.getByTestId(id);
    await expect(tab).toBeVisible();
    const box = await tab.boundingBox();
    expect(box).not.toBeNull();
    // The tab must not overflow the dialog's right edge (the old layout bug).
    expect(box!.x + box!.width).toBeLessThanOrEqual(dialogBox!.x + dialogBox!.width + 1);
  }

  // Clicking the YouTube tab reveals its search field.
  await page.getByTestId("tab-youtube").click();
  await expect(page.getByTestId("youtube-query")).toBeVisible();
});
