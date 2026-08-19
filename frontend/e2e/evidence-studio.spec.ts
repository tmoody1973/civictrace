import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const CASE_ID = "case-tid121-bronzeville-arts-tech-hub";
const STUDIO = `/cases/${CASE_ID}`;

async function expectNoSeriousAxeViolations(page: Page, scope: string) {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious, `${scope}: ${serious.map((v) => `${v.id} (${v.nodes.length})`).join(", ")}`).toEqual([]);
}

test.describe("Evidence Studio — TID 121 replay", () => {
  test("mouse path: card → trace → NOT_PUBLISHED → $2,345,000 anchor → PDF page 3 → Matches ledger", async ({ page }) => {
    await page.goto(STUDIO);

    // Promise Card + Decision Delta, in words
    await expect(page.getByTestId("state-badge")).toHaveText(/Change staged — awaiting human review/);
    await expect(page.getByTestId("delta-summary")).toContainText("$700,000");
    await expect(page.getByTestId("delta-summary")).toContainText("$2,345,000");
    await expect(page.getByTestId("delta-next-evidence")).toContainText("2025 Annual Report");
    await expectNoSeriousAxeViolations(page, "studio loaded");

    // Evidence Trace, collapsed by default → open → honest gap visible
    const toggle = page.getByRole("button", { name: "Toggle Evidence Trace" });
    await expect(toggle).toContainText("Evidence Trace · 16 rows · 3 source artifacts");
    await expect(page.getByRole("list", { name: "Ledger rows" })).toHaveCount(0);
    await toggle.click();
    const notPublished = page.getByTestId("trace-row-ARTIFACT_NOT_PUBLISHED");
    await expect(notPublished).toBeVisible();
    await expect(notPublished).toContainText("NOT_PUBLISHED");
    await expect(notPublished).toContainText("Absence of the record is recorded as NOT_PUBLISHED");
    await expect(page.getByTestId("trace-row-DELTA_STAGED")).toHaveAttribute("data-human-step", "true");
    await expectNoSeriousAxeViolations(page, "trace expanded");

    // Anchor → real PDF page 3 → hash proof
    await page.getByRole("button", { name: "Open tid121-amendment-1-2026 at page 3" }).first().click();
    await expect(page.getByTestId("artifact-header")).toContainText("tid121-amendment-1-2026");
    await expect(page.getByTestId("page-label")).toHaveText(/Page 3 of \d+/);
    await expect(page.getByTestId("anchored-page-badge")).toHaveText("Anchored page 3");
    await expect(page.getByTestId("hash-verdict")).toHaveAttribute("data-verdict", "match");
    await expect(page.getByTestId("hash-verdict")).toContainText("Matches ledger");
    await expect(page.locator(".react-pdf__Page canvas")).toBeVisible();
    await page.screenshot({ path: "test-results/studio-page3-matches-ledger.png", fullPage: false });

    // Delta chip → trace highlights the matching evidence row
    await page.getByRole("button", { name: "Show evidence ev-tid121-plan-capital-costs in the Evidence Trace" }).click();
    await expect(page.locator('[data-evidence-id="ev-tid121-plan-capital-costs"]')).toHaveClass(/ring-2/);
  });

  test("keyboard-only path: Tab/Enter opens the trace and jumps to an anchored page", async ({ page }) => {
    await page.goto(STUDIO);
    await expect(page.getByTestId("state-badge")).toBeVisible();

    // Walk with Tab until the trace toggle has focus, press Enter
    await focusByTab(page, 'button[aria-label="Toggle Evidence Trace"]');
    await page.keyboard.press("Enter");
    await expect(page.getByRole("list", { name: "Ledger rows" })).toBeVisible();

    // Keep tabbing to the first page-anchored button in the trace, press Enter
    await focusByTab(page, '[data-testid="anchor-jump"][aria-label*="at page "]');
    const label = await page.evaluate(() => document.activeElement?.getAttribute("aria-label"));
    const expectedPage = Number(/at page (\d+)/.exec(label ?? "")?.[1]);
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("page-label")).toHaveText(new RegExp(`Page ${expectedPage} of \\d+`));
    await expect(page.getByTestId("page-announcement")).toContainText("this is the anchored page");

    // Page controls are reachable and work from the keyboard
    await page.getByRole("button", { name: "Next page" }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("page-label")).toHaveText(new RegExp(`Page ${expectedPage + 1} of \\d+`));
  });

  test("API down: every pane says so in words, nothing is blank", async ({ page }) => {
    await page.route("**/localhost:8000/**", (route) => route.abort("connectionrefused"));
    await page.goto(STUDIO);
    const alerts = page.getByRole("alert").filter({ hasText: "Cannot reach the CivicTrace API" });
    await expect(alerts.first()).toBeVisible();
    expect(await alerts.count()).toBeGreaterThanOrEqual(3); // rail, source pane, review pane, trace
    await expect(page.getByText("Nothing is shown rather than something unverified.").first()).toBeVisible();
  });
});

/** Press Tab until the active element matches `selector` (bounded), so the test never uses the mouse. */
async function focusByTab(page: Page, selector: string, maxTabs = 60) {
  for (let i = 0; i < maxTabs; i++) {
    if (await page.evaluate((sel) => document.activeElement?.matches(sel) ?? false, selector)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error(`Tabbed ${maxTabs} times without reaching ${selector}`);
}
