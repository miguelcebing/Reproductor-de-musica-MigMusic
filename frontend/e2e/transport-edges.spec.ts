/** PLAYLIST-009 = A: the transport never greys out and explains its edges.

 * The backend flags disable the manual skip at the head/tail; the UI keeps the
 * buttons live and answers with a toast instead of stopping the music.
 */

import { expect, test } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

const ONE = makeWav("Edge One");
const TWO = makeWav("Edge Two");

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("next and previous stay enabled and explain both edges", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await page.goto("/");
  await page.getByTestId("playlist-name").fill("Edge Mix");
  await page.getByTestId("playlist-create").click();

  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([ONE, TWO]);
  await page.getByTestId("dialog-submit").click();
  await expect(page.getByTestId("track-row")).toHaveCount(2);

  // Seek reads as a step, not as an arrow.
  await expect(page.getByTestId("skip-forward")).toContainText("+5 s");
  await expect(page.getByTestId("skip-forward")).toHaveAttribute("aria-label", "Adelantar 5 s");
  await expect(page.getByTestId("skip-backward")).toContainText("-5 s");
  await expect(page.getByTestId("skip-backward")).toHaveAttribute("aria-label", "Retroceder 5 s");

  await page.getByRole("button", { name: "Reproducir Edge One" }).click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Edge One");

  // Middle of the list: both buttons are live.
  await expect(page.getByTestId("next")).toBeEnabled();
  await expect(page.getByTestId("previous")).toBeEnabled();
  await page.getByTestId("next").click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Edge Two");

  // Tail: still enabled, and the click explains itself without stopping music.
  await expect(page.getByTestId("next")).toBeEnabled();
  await page.getByTestId("next").click();
  await expect(page.getByTestId("toasts")).toContainText("Estás en la última canción");
  await expect(page.getByTestId("now-playing-title")).toHaveText("Edge Two");
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Pausar");

  await page.getByTestId("previous").click();
  await expect(page.getByTestId("now-playing-title")).toHaveText("Edge One");

  // Head: the same story backwards.
  await expect(page.getByTestId("previous")).toBeEnabled();
  await page.getByTestId("previous").click();
  await expect(page.getByTestId("toasts")).toContainText("Estás en la primera canción");
  await expect(page.getByTestId("now-playing-title")).toHaveText("Edge One");
  await expect(page.getByTestId("play-pause")).toHaveAttribute("aria-label", "Pausar");

  expect(pageErrors, `page errors: ${pageErrors.join(" | ")}`).toHaveLength(0);
});
