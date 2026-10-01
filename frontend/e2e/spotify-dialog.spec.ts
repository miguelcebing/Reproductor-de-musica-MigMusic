/** UX-003: the add-music dialog keeps its submit button reachable.

 * Spotify is stubbed at the route level so the run stays hermetic while the
 * real backend stores whatever is added.
 */

import { expect, test, type Page } from "@playwright/test";
import { resetBackend } from "./helpers";

interface StubSong {
  readonly id: string;
  readonly title: string;
  readonly artist: string;
  readonly source: string;
  readonly duration: number;
  readonly duration_label: string;
  readonly album: string | null;
  readonly artwork_url: string | null;
  readonly external_url: string | null;
  readonly available: boolean;
  readonly favorite: boolean;
}

function stubSong(index: number): StubSong {
  return {
    id: `sp-${index}`,
    title: `Spotify Track ${index}`,
    artist: "Stub Artist",
    source: "spotify",
    duration: 180,
    duration_label: "3:00",
    album: null,
    artwork_url: null,
    external_url: null,
    available: true,
    favorite: false,
  };
}

const RESULTS: StubSong[] = Array.from({ length: 10 }, (_, index) => stubSong(index + 1));

/** Pretend the session is linked and the catalog always returns 10 tracks. */
async function stubSpotify(page: Page): Promise<void> {
  await page.route("**/api/auth/spotify/status", (route) =>
    route.fulfill({ json: { authenticated: true } }),
  );
  await page.route("**/api/spotify/search**", (route) => route.fulfill({ json: RESULTS }));
}

async function expectInsideViewport(page: Page): Promise<void> {
  const submit = page.getByTestId("dialog-submit");
  const box = await submit.boundingBox();
  const viewport = page.viewportSize();
  expect(box, "submit button must be laid out").not.toBeNull();
  expect(viewport, "viewport must be known").not.toBeNull();
  const bottom = (box as NonNullable<typeof box>).y + (box as NonNullable<typeof box>).height;
  expect(bottom, "submit button must not hang below the fold").toBeLessThanOrEqual(
    (viewport as NonNullable<typeof viewport>).height,
  );
  const top = (box as NonNullable<typeof box>).y;
  expect(top, "submit button must not be pushed above the fold").toBeGreaterThanOrEqual(0);
}

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("the submit button stays on screen with a full page of Spotify results", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await stubSpotify(page);
  await page.goto("/");

  await page.getByTestId("playlist-name").fill("Dialog Mix");
  await page.getByTestId("playlist-create").click();

  await page.getByTestId("add-music").click();
  await page.getByTestId("tab-spotify").click();
  await page.getByTestId("spotify-query").fill("night");
  await page.getByTestId("spotify-search").click();

  await expect(page.getByTestId("spotify-results")).toBeVisible();
  await expect(page.locator("[data-testid^=spotify-result-]")).toHaveCount(10);

  // Without a selection the label stays generic.
  await expect(page.getByTestId("dialog-submit")).toHaveText("Agregar");
  await expectInsideViewport(page);

  // Tick tracks at the top, the bottom and in the middle: the last one is only
  // reachable by scrolling the results, and the actions row must survive it.
  for (const id of ["sp-1", "sp-5", "sp-10"]) {
    await page.getByTestId(`spotify-result-${id}`).check();
  }
  await expect(page.getByTestId("dialog-submit")).toHaveText("Agregar (3)");
  await expectInsideViewport(page);

  await page.getByTestId("dialog-submit").click();

  const rows = page.getByTestId("track-row");
  await expect(rows).toHaveCount(3);
  await expect(rows.first()).toContainText("Spotify Track 1");
  await expect(rows.last()).toContainText("Spotify Track 10");

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
