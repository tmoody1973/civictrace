import { defineConfig, devices } from "@playwright/test";

// Overridable: Tarik's machine runs several Next apps; e2e must never collide with
// (or worse, silently reuse) a different app on 3000. CI keeps the defaults.
const API_PORT = Number(process.env.CIVICTRACE_E2E_API_PORT ?? 8000);
const WEB_PORT = Number(process.env.CIVICTRACE_E2E_WEB_PORT ?? 3000);

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
      // The backend must trust the port the e2e studio actually runs on (CORS),
      // or every browser fetch is refused while curl checks happily pass.
      env: { CIVICTRACE_CORS_ORIGINS: `http://localhost:${WEB_PORT}` },
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
