import { defineConfig, devices } from "@playwright/test";

const API_PORT = 8000;
const WEB_PORT = 3000;

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1, // the live backend session is shared state; approval tests must not race the read tests
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
  webServer: [
    {
      command: "bash e2e/start-backend.sh",
      url: `http://localhost:${API_PORT}/healthz`,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: `pnpm dev --port ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}/`,
      reuseExistingServer: !process.env.CI,
      timeout: 240_000,
      // Explicit values beat .env.local: e2e stays local even when the developer's
      // .env.local points the studio at the cloud API (MOO-711 cloud mode).
      env: { NEXT_PUBLIC_API_BASE_URL: `http://localhost:${API_PORT}`, NEXT_PUBLIC_API_BEARER: "" },
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
});
