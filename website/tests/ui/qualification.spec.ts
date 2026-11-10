import { test, expect, type Browser } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const ROUTES = ["/", "/paper/", "/results/", "/models/", "/methods/", "/evidence/"];
const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "tablet-portrait", width: 834, height: 1112 },
  { id: "tablet-landscape", width: 1112, height: 834 },
  { id: "mobile-portrait", width: 390, height: 844 },
  { id: "mobile-landscape", width: 844, height: 390 },
];

async function audit(browser: Browser, width: number, height: number, route: string) {
  const context = await browser.newContext({ viewport: { width, height }, reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto(route, { waitUntil: "networkidle" });
  // Expand every disclosure so tables and receipts are audited too.
  for (const d of await page.locator("details").all()) await d.evaluate((el) => el.setAttribute("open", ""));
  const result = await new AxeBuilder({ page })
    .withTags(WCAG)
    .exclude("canvas")
    .analyze();
  await context.close();
  return result.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} × ${v.nodes[0]?.target.join(" ")}`);
}

for (const route of ROUTES) {
  test(`axe WCAG 2.2 AA: ${route} desktop and mobile`, async ({ browser }) => {
    test.setTimeout(240_000);
    expect(await audit(browser, 1440, 1000, route), "desktop").toEqual([]);
    expect(await audit(browser, 390, 844, route), "mobile").toEqual([]);
  });
}

test("five viewports: every route loads, keeps navigation and never overflows the page", async ({ browser }) => {
  test.setTimeout(300_000);
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, hasTouch: vp.width < 1200 });
    const page = await context.newPage();
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const route of ROUTES) {
      const res = await page.goto(route, { waitUntil: "networkidle" });
      expect(res?.status(), `${vp.id} ${route}`).toBe(200);
      await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow, `${vp.id} ${route}`).toBeLessThanOrEqual(0);
    }
    expect(errors, vp.id).toEqual([]);
    await context.close();
  }
});

test("keyboard: skip link, area navigation and figure controls are reachable with visible focus", async ({ page }) => {
  await page.goto("/results/");
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main$/);
  await page.goto("/results/");
  const tabsTo = async (selector: string, limit = 40) => {
    for (let i = 0; i < limit; i++) {
      await page.keyboard.press("Tab");
      if (await page.evaluate((sel) => document.activeElement?.matches(sel) ?? false, selector)) return true;
    }
    return false;
  };
  expect(await tabsTo('nav[aria-label="Main navigation"] a[href="/models/"]')).toBe(true);
  const outline = await page.evaluate(() => getComputedStyle(document.activeElement!).outlineStyle);
  expect(outline).not.toBe("none");
  expect(await tabsTo('figure#fig-6 button[aria-pressed]', 80)).toBe(true);
  await page.keyboard.press("Enter");
  await expect(page.locator("figure#fig-6 button[aria-pressed]").first()).toHaveAttribute("aria-pressed", "true");
});

test("figures work with reduced motion and without WebGL", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  await context.addInitScript(() => {
    const proto = HTMLCanvasElement.prototype as unknown as { getContext: (...a: unknown[]) => unknown };
    const original = proto.getContext;
    // Report WebGL as unavailable; 2D contexts keep working.
    proto.getContext = function (this: HTMLCanvasElement, ...args: unknown[]) {
      if (String(args[0]).startsWith("webgl")) return null;
      return original.apply(this, args);
    };
  });
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const route of ["/results/", "/models/", "/methods/", "/evidence/"]) {
    await page.goto(route, { waitUntil: "networkidle" });
    const figures = page.locator("figure.pub-figure");
    for (const fig of await figures.all()) {
      await expect(fig.locator("svg").first()).toBeVisible();
      await expect(fig.locator("table.pub-table tbody tr").first()).toBeAttached();
    }
  }
  await page.goto("/");
  await expect(page.locator("#overview")).toContainText("0.736270");
  await expect(page.locator("#explorer")).toBeAttached();
  expect(errors).toEqual([]);
  await context.close();
});

test("data tables are reachable alternatives with headers and captions", async ({ page }) => {
  for (const route of ["/results/", "/models/", "/methods/", "/evidence/"]) {
    await page.goto(route);
    for (const details of await page.locator("figure.pub-figure details").all()) {
      const summary = details.locator("summary");
      if (!(await summary.textContent())?.startsWith("Data table")) continue;
      await summary.focus();
      await page.keyboard.press("Enter");
      const table = details.locator("table");
      await expect(table).toBeVisible();
      await expect(table.locator("caption")).not.toBeEmpty();
      expect(await table.locator("thead th[scope=col]").count()).toBeGreaterThan(1);
      await expect(details.getByRole("region")).toHaveAttribute("tabindex", "0");
    }
  }
});
