import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("built frontend connects to actual backend and survives API failure", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Backend connected")).toBeVisible();
  await expect(page.getByText("v0.3.0 · Database reachable")).toBeVisible();
  const ready = await page.request.get("http://127.0.0.1:8000/ready");
  expect(await ready.json()).toEqual({
    status: "ready",
    database: "reachable",
  });
  await page.route("**/ready", (route) =>
    route.fulfill({
      status: 503,
      body: "{}",
      headers: { "Access-Control-Allow-Origin": "http://127.0.0.1:4173" },
    }),
  );
  await page.reload();
  await expect(page.getByText("Backend unavailable")).toBeVisible();
  await page.unroute("**/ready");
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByText("Backend connected")).toBeVisible();
});
test("responsive shell has no overflow or automated accessibility violations", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Backend connected")).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole("button", { name: "Dark theme" }).click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
});

test("explorer reads the isolated synthetic registry on mobile", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await page.getByRole("link", { name: "Data Explorer" }).click();
  await expect(page.getByText("Synthetic fixture · MIT")).toBeVisible();
  await expect(page.getByText("40", { exact: true })).toBeVisible();
  await expect(page.getByText("temporal holdout · Unsupported")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test("analytics pages render actual synthetic aggregates on mobile", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/");
  await page.getByRole("link", { name: "Analytics", exact: true }).click();
  await expect(
    page.getByText(
      "Synthetic fixture · Eligible development observations only",
    ),
  ).toBeVisible();
  await page.getByLabel("Feature", { exact: true }).selectOption("tariff_plan");
  await expect(
    page.getByRole("table", {
      name: "Distribution counts by value or interval",
    }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Feature Lab" }).click();
  await expect(
    page.getByText(/Batch and single-record parity: verified/),
  ).toBeVisible();
  await page.getByRole("link", { name: "Evaluation design" }).click();
  await expect(
    page
      .getByRole("table", { name: "Development validation folds" })
      .locator("tbody tr"),
  ).toHaveCount(5);
  await page.getByRole("button", { name: "Dark theme" }).click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
