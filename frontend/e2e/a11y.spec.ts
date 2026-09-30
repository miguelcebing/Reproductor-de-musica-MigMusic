/** WCAG A/AA scan with axe-core (SKILL6: accessibility level). */

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { makeWav, resetBackend } from "./helpers";

async function expectNoViolations(page: Page, context: string): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const summary = results.violations.map(
    (violation) =>
      `${violation.id} (${violation.impact}): ${violation.help} — ` +
      `${violation.nodes.length} node(s), first: ${violation.nodes[0]?.target.join(" ")}`,
  );
  expect(summary, `${context} must have no WCAG A/AA violations`).toEqual([]);
}

async function seedPage(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByTestId("playlist-name").fill("Accesibilidad");
  await page.getByTestId("playlist-create").click();
  await page.getByTestId("add-music").click();
  await page.getByTestId("file-input").setInputFiles([makeWav("Canción de prueba")]);
  await page.getByTestId("dialog-submit").click();
  await expect(page.getByTestId("track-row")).toHaveCount(1);
}

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test.describe("light theme", () => {
  test("main view with rows and the linked-list panel is WCAG A/AA clean", async ({ page }) => {
    await seedPage(page);
    await page.getByTestId("nodes-toggle").click();
    await expect(page.getByTestId("linked-list-view")).toBeVisible();
    await expectNoViolations(page, "main view (light)");
  });

  test("open add dialog traps focus and closes with Escape", async ({ page }) => {
    await seedPage(page);
    await page.getByTestId("add-music").click();
    const dialog = page.getByTestId("add-dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog).toBeFocused();

    for (let i = 0; i < 25; i += 1) {
      await page.keyboard.press("Tab");
      const inside = await page.evaluate(
        () => document.activeElement?.closest('[data-testid="add-dialog"]') !== null,
      );
      expect(inside, `focus escaped the dialog on Tab #${i + 1}`).toBe(true);
    }

    await expectNoViolations(page, "add dialog (light)");

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
  });
});

test.describe("dark theme", () => {
  test.use({ colorScheme: "dark" });

  test("main view is WCAG A/AA clean", async ({ page }) => {
    await seedPage(page);
    await expectNoViolations(page, "main view (dark)");
  });
});
