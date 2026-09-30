import { defineConfig, devices } from "@playwright/test";

const PORT = 5173;
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  // The backend keeps one global playback state: run specs one at a time.
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    // Local playback starts from click handlers after async API calls (F5/F7).
    launchOptions: {
      args: ["--autoplay-policy=no-user-gesture-required"],
    },
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      testMatch: /master-flow\.spec\.ts/,
      use: { ...devices["Pixel 7"] },
    },
  ],
  webServer: [
    {
      command: "npx vite --port 5173",
      url: BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: "uv run uvicorn migmusic.main:app --host 127.0.0.1 --port 8000",
      cwd: "../backend",
      url: "http://127.0.0.1:8000/api/health",
      // Hermetic settings: no .env needed locally or in CI, and an empty
      // DATABASE_URL keeps the E2E run on the in-memory repository.
      env: {
        APP_ENV: "development",
        LOG_LEVEL: "WARNING",
        FRONTEND_ORIGIN: "http://127.0.0.1:5173",
        ALLOWED_ORIGINS: "http://127.0.0.1:5173",
        SPOTIFY_CLIENT_ID: "e2e-client-id",
        SPOTIFY_CLIENT_SECRET: "e2e-client-secret",
        SPOTIFY_REDIRECT_URI: "http://127.0.0.1:5173/callback",
        SESSION_SECRET_KEY: "migmusic-e2e-session-secret-key-0123456789",
        DATABASE_URL: "",
      },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
