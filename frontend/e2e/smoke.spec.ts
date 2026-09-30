import { expect, test } from "@playwright/test";
import { resetBackend } from "./helpers";

test.beforeEach(async ({ request }) => {
  await resetBackend(request);
});

test("health check reaches the backend through the dev proxy", async ({ page }) => {
  const response = await page.request.get("/api/health");
  expect(response.ok()).toBe(true);
  expect(await response.json()).toMatchObject({ status: "ok" });
});

test("boots with the Spanish UI and an empty state", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("MigMusic");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.getByTestId("language-toggle")).toBeVisible();
  await expect(page.getByTestId("theme-toggle")).toBeVisible();
  await expect(page.getByTestId("playlist-create")).toBeDisabled();
});
