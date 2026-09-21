import { test, expect } from "@playwright/test";

test.describe("M1.4-D Email Workflows", () => {
  test("displays the email workflow portfolio", async ({ page }) => {
    await page.route("**/api/operations-center/email-workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "ready",
          scheduler: {
            running: true,
            adapter_enabled: true,
          },
          provider: {
            status: "ready",
          },
          count: 1,
          workflows: [
            {
              workflow_id: "EMAIL-WF-001",
              name: "Daily Compliance Summary",
              description: "Daily compliance summary email.",
              workflow_type: "scheduled",
              lifecycle: "active",
              owner: "Compliance",
              trigger: "Daily schedule",
              schedule: "0 8 * * *",
              template_id: "TPL-COMPLIANCE-001",
              version: 1,
              created_at: "2026-09-18T08:00:00Z",
              updated_at: "2026-09-18T08:00:00Z",
              registered: true,
              enabled: true,
              operational_status: "ready",
              next_run: "2026-09-19T08:00:00Z",
            },
          ],
        }),
      });
    });

    await page.goto("/operations-center/email-workflows");

    await expect(
      page.getByRole("heading", { name: "Email Workflows" }),
    ).toBeVisible();

    await expect(
      page.getByText("Daily Compliance Summary"),
    ).toBeVisible();

    await expect(
      page.getByText("Compliance", { exact: true }),
    ).toBeVisible();

    await expect(
      page.getByText("Read-only", { exact: true }),
    ).toBeVisible();
  });

  test("handles backend authorization failure", async ({ page }) => {
    await page.route("**/api/operations-center/email-workflows", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Forbidden",
        }),
      });
    });

    await page.goto("/operations-center/email-workflows");

    await expect(
      page.getByText(/not authorized|forbidden|permission/i),
    ).toBeVisible();
  });

  test("does not expose workflow mutation controls", async ({ page }) => {
    await page.route("**/api/operations-center/email-workflows", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "ready",
          scheduler: {
            running: true,
            adapter_enabled: true,
          },
          provider: {
            status: "ready",
          },
          count: 0,
          workflows: [],
        }),
      });
    });

    await page.goto("/operations-center/email-workflows");

    await expect(
      page.getByRole("heading", { name: "Email Workflows" }),
    ).toBeVisible();

    await expect(
      page.getByRole("button", { name: /create/i }),
    ).toHaveCount(0);

    await expect(
      page.getByRole("button", { name: /pause/i }),
    ).toHaveCount(0);

    await expect(
      page.getByRole("button", { name: /resume/i }),
    ).toHaveCount(0);

    await expect(
      page.getByRole("button", { name: /disable/i }),
    ).toHaveCount(0);

    await expect(
      page.getByRole("button", { name: /enable/i }),
    ).toHaveCount(0);
  });
});
