import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// The intake UI against a stubbed API: CI has no network to Legistar, and the refusal
// paths are proven by backend tests; here we prove the journalist-facing flow and words.

const BUNDLE = {
  bundle_id: "bundle-260433-e2e",
  legistar_file: "260433",
  matter_id: 74415,
  title: "Substitute resolution approving Amendment No. 1 to the TID 121 Project Plan",
  matter_type: "Resolution",
  matter_status: "Passed",
  intro_date: "2026-06-17",
  matter_url: "https://webapi.legistar.com/v1/milwaukee/matters/74415",
  attachments: [
    {
      attachment_id: 248545,
      name: "Amendment",
      url: "https://milwaukee.legistar1.com/milwaukee/attachments/a.pdf",
    },
    {
      attachment_id: 248546,
      name: "Fiscal note",
      url: "https://milwaukee.legistar1.com/milwaukee/attachments/b.pdf",
    },
  ],
  retrieved_at: "2026-08-21T14:00:00Z",
  status: "DRAFT",
  failure_reason: null,
  case_id: null,
};

function envelope(data: unknown) {
  return { ok: true, data, error: null };
}

const SEARCH_RESULTS = [
  {
    legistar_file: "260433",
    matter_id: 74415,
    title: "Substitute resolution approving Amendment No. 1 to the TID 121 Project Plan",
    matter_type: "Resolution",
    matter_status: "Passed",
    intro_date: "2026-06-17",
  },
];

async function stubIntake(page: Page) {
  let approved = false;
  await page.route("**/intake/search", (route) => {
    const body = route.request().postDataJSON() as { query: string };
    return route.fulfill({
      json: envelope(body.query.toLowerCase().includes("amendment") ? SEARCH_RESULTS : []),
    });
  });
  await page.route("**/intake/lookup", (route) => {
    const body = route.request().postDataJSON() as { file_number: string };
    if (body.file_number !== "260433") {
      return route.fulfill({
        status: 422,
        json: { ok: false, data: null, error: "the official Legistar record lists no matter with that file" },
      });
    }
    return route.fulfill({ json: envelope(BUNDLE) });
  });
  await page.route("**/intake/bundles/bundle-260433-e2e/approve", (route) => {
    approved = true;
    return route.fulfill({ json: envelope({ ...BUNDLE, status: "APPROVED" }) });
  });
  await page.route("**/intake/bundles/bundle-260433-e2e", (route) =>
    route.fulfill({
      json: envelope(
        approved
          ? { ...BUNDLE, status: "CASE_CREATED", case_id: "case-intake-260433" }
          : BUNDLE,
      ),
    }),
  );
}

test.describe("Case intake — start your own case", () => {
  test("lookup → review roles → approve → case link appears", async ({ page }) => {
    await stubIntake(page);
    await page.goto("/intake");

    await page.getByLabel("What are you looking into?").fill("TID 121 amendment");
    await page.getByRole("button", { name: "Search the record" }).click();
    await expect(page.getByTestId("search-results")).toContainText("File 260433");
    await page.getByRole("button", { name: "Review file 260433" }).click();
    await expect(page.getByTestId("candidate-bundle")).toContainText("Amendment No. 1");
    await expect(page.getByTestId("candidate-bundle")).toContainText("Fiscal note");

    // Approve stays locked until the human review is complete
    const approveButton = page.getByRole("button", { name: "Approve — create this case" });
    await expect(approveButton).toBeDisabled();
    await page.getByLabel("Role for Amendment").selectOption("promise");
    await page
      .getByLabel("What is this case about? (the case topic)")
      .fill("The commitment in file 260433 and its public follow-through");
    await page.getByLabel("Your name (recorded as the reviewer)").fill("Tarik Moody");
    await expect(approveButton).toBeEnabled();

    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, serious.map((v) => v.id).join(", ")).toEqual([]);

    await approveButton.click();
    await expect(page.getByText("Case created")).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByRole("link", { name: "Open the case in the Evidence Studio" }),
    ).toHaveAttribute("href", "/cases/case-intake-260433");
  });

  test("no matches: honest empty state with advice, nothing invented", async ({ page }) => {
    await stubIntake(page);
    await page.goto("/intake");
    await page.getByLabel("What are you looking into?").fill("unfindable topic words");
    await page.getByRole("button", { name: "Search the record" }).click();
    await expect(page.getByTestId("search-empty")).toContainText("lists nothing with those words");
  });
});
