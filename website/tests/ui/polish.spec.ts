import { test, expect } from "@playwright/test";
import { decaySlope } from "../../src/lib/decay.mjs";

test("plot selection links to the existing controls and tooltips identify the metric", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#explorer");
  await page.selectOption("#root-select", "C");
  await page.locator(".chart .recharts-line-dot").last().click();
  await expect(page.getByRole("button", { name: "H72", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".chart .recharts-default-tooltip")).toContainText("H72 · Force · NRMSE · Root C");
  await expect(page.locator(".chart .recharts-tooltip-item-value").first()).toHaveText(/^\d+\.\d{6}$/);
  await page.getByRole("button", { name: "RMSE", exact: true }).click();
  await page.locator(".chart .recharts-line-dot").last().hover();
  await expect(page.locator(".chart .recharts-tooltip-item-value").first()).toHaveText(/^\d+\.\d{6} N\/kg$/);
});

test("touch plot picking, signed axes and derivative precision work on mobile", async ({ browser }) => {
  const context = await browser.newContext({ baseURL: "http://127.0.0.1:4174", viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("/#lab");
  await page.getByRole("button", { name: "Opposing modes", exact: true }).tap();
  await page.locator(".lab-chart").scrollIntoViewIfNeeded();
  const ticks = await page.locator(".lab-chart .recharts-cartesian-axis-tick-value").allTextContents();
  expect(ticks.some((t) => Number(t) < 0)).toBe(true);
  expect(ticks.some((t) => Number(t) > 0)).toBe(true);
  await page.getByRole("button", { name: "Rate of change", exact: true }).tap();
  await page.locator(".lab-chart").scrollIntoViewIfNeeded();
  const grid = (await page.locator(".lab-chart .recharts-cartesian-grid").boundingBox())!;
  await page.touchscreen.tap(grid.x + grid.width / 2, grid.y + grid.height / 2);
  await expect(page.locator("#lab-time")).not.toHaveValue("24");
  const hour = Number(await page.locator("#lab-time").inputValue());
  expect(hour).toBeGreaterThanOrEqual(83);
  expect(hour).toBeLessThanOrEqual(85);
  await expect(page.locator(".lab-chart .recharts-tooltip-item-value").first()).toHaveText(decaySlope(hour, -0.7, 0.3).toFixed(6));
  const tooltip = (await page.locator(".lab-chart .recharts-default-tooltip").boundingBox())!;
  expect(tooltip.x).toBeGreaterThanOrEqual(0);
  expect(tooltip.x + tooltip.width).toBeLessThanOrEqual(390);
  await context.close();
});
