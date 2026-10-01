/** Local playlists are scoped per device (`UX-010`), not per user.

 * Two isolated browser contexts get two `mig_device_id`s, so neither one can
 * see the other's lists. This is UX isolation, not authentication: the header
 * is advisory and the unscoped view (no header) still returns everything.
 */

import { expect, test, type Page } from "@playwright/test";
import { resetBackend } from "./helpers";

function deviceId(page: Page): Promise<string | null> {
  return page.evaluate(() => window.localStorage.getItem("mig_device_id"));
}

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("each browser context keeps its own playlists", async ({ page, browser }) => {
  const secondContext = await browser.newContext();
  const other = await secondContext.newPage();

  try {
    await page.goto("/");
    await other.goto("/");

    // Two contexts, two persisted ids.
    await expect.poll(() => deviceId(page)).toBeTruthy();
    await expect.poll(() => deviceId(other)).toBeTruthy();
    expect(await deviceId(page)).not.toBe(await deviceId(other));

    // Device A creates its list.
    await page.getByTestId("playlist-name").fill("Phone mix");
    await page.getByTestId("playlist-create").click();
    await expect(page.getByTestId("playlist-select")).toContainText("Phone mix");

    // Device B starts empty: A's list never crossed over.
    await expect(other.getByTestId("playlist-select")).not.toContainText("Phone mix");
    await expect(other.getByTestId("empty-state")).toBeVisible();

    // Device B creates its own; each side keeps only its own.
    await other.getByTestId("playlist-name").fill("Laptop mix");
    await other.getByTestId("playlist-create").click();
    await expect(other.getByTestId("playlist-select")).toContainText("Laptop mix");

    await expect(other.getByTestId("playlist-select")).not.toContainText("Phone mix");
    await expect(page.getByTestId("playlist-select")).toContainText("Phone mix");
    await expect(page.getByTestId("playlist-select")).not.toContainText("Laptop mix");
  } finally {
    await secondContext.close();
  }
});
