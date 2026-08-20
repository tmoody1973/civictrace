// The approval boundary, on camera and in CI: the system drafts, a human approves the exact
// bytes, and a wrong approval is refused in words. Runs against the live in-process session
// (CIVICTRACE_LIVE=1, fake agent runner, no cloud). Serial: the approve test mutates the
// shared session, so it runs last.

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const CASE_ID = "case-tid121-bronzeville-arts-tech-hub";
const STUDIO = `/cases/${CASE_ID}`;
const REFUSAL_WORDS = "you approved different bytes than are staged";

test.describe.configure({ mode: "serial" });

async function expectNoSeriousAxeViolations(page: Page, scope: string) {
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(serious, `${scope}: ${serious.map((v) => `${v.id} (${v.nodes.length})`).join(", ")}`).toEqual([]);
}

async function openDrawer(page: Page) {
  await page.goto(STUDIO);
  const drawer = page.getByTestId("approval-drawer");
  await expect(drawer).toBeVisible();
  await drawer.scrollIntoViewIfNeeded();
  return drawer;
}

test.describe("Approval boundary — TID 121 live session", () => {
  test("the drawer shows the staged question, its exact hash, and the expiry rule", async ({ page }) => {
    const drawer = await openDrawer(page);
    await expect(drawer.getByTestId("staged-question")).toContainText("2025 Annual Report of Tax Incremental Districts");
    await expect(drawer.getByTestId("proposal-hash")).toContainText(/^sha256:[0-9a-f]{64}$/);
    await expect(drawer).toContainText("An approval expires 30 minutes after it is issued.");
    await expect(drawer).toContainText("No student-level information.");
    await expect(page.getByText("No packet rendered")).toBeVisible();
    await expectNoSeriousAxeViolations(page, "drawer staged");
  });

  test("failed approval: a tampered hash echo is refused in words, nothing renders", async ({ page }) => {
    // Rewrite the POST body in flight so the server genuinely receives the wrong bytes.
    await page.route("**/inquiry/approve", async (route) => {
      const body = JSON.parse(route.request().postData() ?? "{}");
      body.artifact_hash = "sha256:" + "0".repeat(64);
      await route.continue({ postData: JSON.stringify(body) });
    });
    const drawer = await openDrawer(page);
    await drawer.getByRole("textbox").first().fill("Tarik Moody");
    await drawer.getByTestId("approve-button").click();
    const refused = drawer.getByTestId("approval-refused");
    await expect(refused).toContainText(REFUSAL_WORDS);
    await expect(refused).toContainText("The system fails closed.");
    await expect(page.getByTestId("packet-view")).toHaveCount(0);
    await refused.screenshot({ path: "test-results/moo-706-refusal-state.png" });
    await page.unroute("**/inquiry/approve");

    // The refusal is a ledger row, not just a toast.
    await page.reload();
    await page.getByRole("button", { name: "Toggle Evidence Trace" }).click();
    const refusedRow = page.getByTestId("trace-row-APPROVAL_REFUSED").first();
    await expect(refusedRow).toContainText(REFUSAL_WORDS);
    await expectNoSeriousAxeViolations(page, "refusal state");
  });

  test("reject path: a note is required, recorded, and no packet exists", async ({ page }) => {
    const drawer = await openDrawer(page);
    const inputs = drawer.getByRole("textbox");
    await inputs.first().fill("Tarik Moody");
    await drawer.getByTestId("reject-button").click();
    await expect(drawer.getByRole("alert")).toContainText("A rejection needs a note.");
    await inputs.nth(1).fill("Scope is wider than the staged delta supports.");
    await drawer.getByTestId("reject-button").click();
    await expect(drawer.getByTestId("approval-rejected")).toContainText("Rejected — recorded in the ledger");
    await expect(page.getByText("No packet rendered")).toBeVisible();

    await page.reload();
    await page.getByRole("button", { name: "Toggle Evidence Trace" }).click();
    await expect(page.getByTestId("trace-row-INQUIRY_APPROVAL_REJECTED").first()).toContainText(
      "Scope is wider than the staged delta supports.",
    );
  });

  test("keyboard-only approve: Tab to the name field, type, Tab to Approve, Enter → DRAFT packet", async ({ page }) => {
    const drawer = await openDrawer(page);
    await focusByTab(page, '[data-testid="approval-drawer"] input[type="text"]');
    await page.keyboard.type("Tarik Moody");
    await focusByTab(page, '[data-testid="approve-button"]');
    await page.keyboard.press("Enter");

    await expect(drawer.getByTestId("approval-approved")).toContainText("Approved — DRAFT packet rendered");
    await expect(drawer.getByTestId("approval-approved")).toContainText(/tok_[0-9a-f]+/);
    const packet = page.getByTestId("packet-view");
    await expect(packet).toBeVisible();
    await expect(packet.getByTestId("draft-banner")).toContainText("DRAFT ONLY — not sent; no external action taken.");
    await expect(packet.getByTestId("packet-hash")).toContainText(/^sha256:[0-9a-f]{64}$/);
    await expect(packet).toContainText("Has the 2025 Annual Report of Tax Incremental Districts");
    await expect(packet).toContainText("anchored excerpts");
    await packet.scrollIntoViewIfNeeded();
    await packet.screenshot({ path: "test-results/moo-706-packet-view.png" });
    await expectNoSeriousAxeViolations(page, "packet view");

    // The human steps are ledger rows the trace shows.
    await page.reload();
    await page.getByRole("button", { name: "Toggle Evidence Trace" }).click();
    await expect(page.getByTestId("trace-row-INQUIRY_APPROVAL_ISSUED").first()).toBeVisible();
    await expect(page.getByTestId("trace-row-PACKET_RENDERED").first()).toContainText("DRAFT packet rendered");
  });
});

/** Press Tab until the active element matches `selector` (bounded), so the test never uses the mouse. */
async function focusByTab(page: Page, selector: string, maxTabs = 80) {
  for (let i = 0; i < maxTabs; i++) {
    if (await page.evaluate((sel) => document.activeElement?.matches(sel) ?? false, selector)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error(`Tabbed ${maxTabs} times without reaching ${selector}`);
}
