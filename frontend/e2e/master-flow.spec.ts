/** SKILL6 master flow: the critical end-to-end journey, desktop + mobile. */

import { expect, test, type Page } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const ALPHA = makeWav("Alpha Take");
const BETA = makeWav("Beta Groove");
const GAMMA = makeWav("Gamma Line");
const DELTA = makeWav("Delta Bridge");

function progressValue(page: Page): Promise<number> {
  return page
    .getByTestId("progress-track")
    .getAttribute("aria-valuenow")
    .then((value) => Number(value ?? 0));
}

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("master flow: add, play, transport, seek, volume, insert, search, remove", async ({
  page,
}) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await page.goto("/");

  // --- Playlist bootstrap (PLAYLIST-001 = B) -----------------------------
  await page.getByTestId("playlist-name").fill("E2E Mix");
  await page.getByTestId("playlist-create").click();

  // --- Add three local tracks at the end (LOCAL-002, UX-003) -------------
  await page.getByTestId("add-music").click();
  await expect(page.getByTestId("add-dialog")).toBeVisible();
  await page.getByTestId("file-input").setInputFiles([ALPHA, BETA, GAMMA]);
  await page.getByTestId("dialog-submit").click();
  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(3);
  await expect(rows.nth(0)).toContainText("Alpha Take");
  await expect(rows.nth(1)).toContainText("Beta Groove");
  await expect(rows.nth(2)).toContainText("Gamma Line");

  // --- Play the first track (RF-04) --------------------------------------
  await page.getByRole("button", { name: "Reproducir Alpha Take" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Alpha Take");
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Pausar");
  await expect
    .poll(() => progressValue(page), { timeout: 15_000 })
    .toBeGreaterThan(0);

  // --- Next / previous (RF-03) -------------------------------------------
  await page.getByTestId("next").click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Beta Groove");
  await page.getByTestId("previous").click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Alpha Take");

  // --- Skip forward exactly SKIP_SECONDS (PLAYER-001) --------------------
  const beforeSkip = await progressValue(page);
  await page.getByTestId("skip-forward").click();
  await expect
    .poll(() => progressValue(page), { timeout: 10_000 })
    .toBeGreaterThanOrEqual(beforeSkip + 4);

  // --- Seek by clicking the bar (PLAYER-007) -----------------------------
  // At max scroll the sticky header can cover the seek bar (mobile): pull it
  // clear of the header before clicking, otherwise the click hits the header.
  await page
    .getByTestId("progress-track")
    .evaluate((element) => element.scrollIntoView({ block: "center" }));
  const box = await page.getByTestId("progress-track").boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.click(box!.x + box!.width * 0.66, box!.y + box!.height / 2);
  await expect.poll(() => progressValue(page), { timeout: 10_000 }).toBeGreaterThanOrEqual(6);
  await expect.poll(() => progressValue(page)).toBeLessThanOrEqual(10);

  // --- Skip backward inside the same track (PLAYER-002 / 002a) -----------
  const beforeBack = await progressValue(page);
  await page.getByTestId("skip-backward").click();
  await expect
    .poll(() => progressValue(page), { timeout: 10_000 })
    .toBeLessThanOrEqual(beforeBack - 3);
  await expect.poll(() => progressValue(page)).toBeGreaterThanOrEqual(beforeBack - 6);
  await expect(page.getByTestId("now-playing-title")).toHaveText("Alpha Take");

  // --- Volume and mute (PLAYER-008) --------------------------------------
  const volume = page.getByTestId("volume");
  await volume.focus();
  await volume.press("End");
  await expect(volume).toHaveValue("100");
  await page.getByTestId("mute").click();
  await expect(volume).toHaveValue("0");
  await page.getByTestId("mute").click();
  await expect(volume).toHaveValue("100");

  // --- In-list search with Enter (FEAT-001-c) ----------------------------
  const search = page.getByTestId("track-search");
  await search.fill("Gamma");
  await expect(rows).toHaveCount(1);
  await search.press("Enter");
  await expect(rows.first()).toHaveAttribute("data-match", "true");
  await search.fill("");
  await expect(rows).toHaveCount(3);

  // --- Insert one track at index 1 (UX-003) ------------------------------
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([DELTA]);
  await page.getByTestId("position-index").click();
  await page.getByRole("spinbutton", { name: "Índice" }).fill("1");
  await page.getByTestId("dialog-submit").click();
  await expect(rows).toHaveCount(4);
  await expect(rows.nth(1)).toContainText("Delta Bridge");

  // --- Favorite toggle (FEAT-001-b) --------------------------------------
  const favorite = page.getByTestId("favorite-0");
  await expect(favorite).toHaveAttribute("aria-pressed", "false");
  await favorite.click();
  await expect(favorite).toHaveAttribute("aria-pressed", "true");

  // --- Didactic linked-list view (UX-002) --------------------------------
  await page.getByTestId("nodes-toggle").click();
  const nodes = page.getByTestId("linked-list-view");
  await expect(nodes).toBeVisible();
  await expect(nodes).toContainText("Delta Bridge");
  await expect(nodes.locator('[data-current="true"]')).toHaveText("Alpha Take");

  // --- Remove the current song (PLAYLIST-009b) ---------------------------
  const activeRow = page.locator('[data-testid="track-row"][data-active="true"]');
  await expect(activeRow).toHaveCount(1);
  await activeRow.locator('[data-testid^="remove-"]').click();
  await expect(rows).toHaveCount(3);
  await expect(page.getByTestId("now-playing-title")).toHaveText("Delta Bridge", {
    timeout: 10_000,
  });

  // --- Pause (RF-02) ------------------------------------------------------
  await page.getByTestId("play-pause").click();
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Reproducir");

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
