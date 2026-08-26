import { test, expect } from "@playwright/test";

const templates = [
  {
    template_id: "beta-update",
    name: "Beta Update",
    category: "Beta",
    description: "Official Beta update pattern.",
    version: 2,
    publication_type: "beta_update",
    fields: [
      {
        name: "body",
        required: true,
        label: "Body",
        multiline: true,
      },
      {
        name: "headline",
        required: true,
        label: "Headline",
        multiline: false,
      },
      {
        name: "timing",
        required: false,
        label: "Timing",
        multiline: false,
      },
    ],
  },
];

test.describe("WS-22.2.x template-driven publication editor", () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      "**/api/announcement-operations/template-editor/templates",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(templates),
        });
      },
    );

    await page.route(
      "**/api/announcement-operations/template-editor/preview",
      async (route) => {
        const body = JSON.parse(route.request().postData() ?? "{}");

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            template_id: body.template_id,
            template_version: body.template_version,
            publication_type: "beta_update",
            content:
              "EASYCHATBOT ACADEMY\n\nBeta 2\n\nTesting starts today.\n\nToday",
          }),
        });
      },
    );

    await page.route(
      "**/api/announcement-operations/template-editor/drafts",
      async (route) => {
        const body = JSON.parse(route.request().postData() ?? "{}");

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "pub-test-001",
            title: body.title,
            content: "rendered",
            template_id: body.template_id,
            template_version: body.template_version,
            publication_type: "beta_update",
            status: "draft",
            created_at: new Date().toISOString(),
          }),
        });
      },
    );
  });

  test("loads approved templates into a dropdown", async ({ page }) => {
    await page.goto("/operations-center/announcement-operations/create");

    await expect(
      page.getByLabel("Approved template"),
    ).toBeVisible();

    await expect(
      page.getByRole("option", { name: /Beta Update · v2/i }),
    ).toBeVisible();

    await expect(page.getByText("Official Beta update pattern.")).toBeVisible();
    await expect(page.getByText("Beta")).toBeVisible();
  });

  test("loads controlled fields and validates required values", async ({
    page,
  }) => {
    await page.goto("/operations-center/announcement-operations/create");

    await expect(page.getByLabel("Headline")).toBeVisible();
    await expect(page.getByLabel("Body")).toBeVisible();
    await expect(page.getByLabel("Timing")).toBeVisible();

    await expect(
      page.getByText(/Complete all required template fields/i),
    ).toBeVisible();

    await expect(
      page.getByRole("button", { name: "Preview" }),
    ).toBeDisabled();
  });

  test("previews the rendered template and saves a draft with version", async ({
    page,
  }) => {
    await page.goto("/operations-center/announcement-operations/create");

    await page.getByLabel("Publication title").fill("Beta 2");
    await page.getByLabel("Headline").fill("Beta 2");
    await page.getByLabel("Body").fill("Testing starts today.");
    await page.getByLabel("Timing").fill("Today");

    await page.getByRole("button", { name: "Preview" }).click();

    await expect(page.getByText("Testing starts today.")).toBeVisible();

    await page.getByRole("button", { name: "Save draft" }).click();

    await expect(
      page.getByText(/saved from beta-update v2/i),
    ).toBeVisible();
  });
});
