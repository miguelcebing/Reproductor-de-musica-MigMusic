/** Native HTML5 drag & drop reordering (`FEAT-001-e`), driven by synthetic events. */

import { expect, test } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const ALPHA = makeWav("Alpha Take");
const BETA = makeWav("Beta Groove");

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("html5 drag reorder works with motion rows", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("playlist-name").fill("Drag");
  await page.getByTestId("playlist-create").click();
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([ALPHA, BETA]);
  await page.getByTestId("dialog-submit").click();
  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(0)).toContainText("Alpha Take");

  const handled = await page.evaluate(() => {
    const list = document.querySelectorAll<HTMLElement>('[data-testid="track-row"]');
    const from = list[0];
    const to = list[1];
    const dataTransfer = new DataTransfer();
    from.dispatchEvent(new DragEvent("dragstart", { bubbles: true, dataTransfer }));
    to.dispatchEvent(
      new DragEvent("dragover", { bubbles: true, cancelable: true, dataTransfer }),
    );
    to.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer }));
    from.dispatchEvent(new DragEvent("dragend", { bubbles: true, dataTransfer }));
    return dataTransfer.getData("text/plain");
  });

  expect(handled).toBe("0");
  await expect(rows.nth(0)).toContainText("Beta Groove");
  await expect(rows.nth(1)).toContainText("Alpha Take");
});
