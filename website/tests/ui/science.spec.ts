import { test, expect } from "@playwright/test";

test("home leads with CMJ science: seven chapters, four scored models, nothing archival first", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("modeling how countermovement-jump outcomes change");
  await expect(page.locator("#overview")).not.toContainText(/Reconstructing a historical/);
  const chapters = await page.locator(".sci-chapters li").allTextContents();
  expect(chapters.map((c) => c.replace(/^\d\s*/, ""))).toEqual([
    "What does a countermovement jump measure?",
    "What happens after training exposure?",
    "How do we model that process?",
    "How was the synthetic experiment designed?",
    "What did the models actually predict?",
    "What can we conclude?",
    "How was the research verified?",
  ]);
  for (const v of ["2.430659", "1.036038", "0.736270", "0.773316"]) await expect(page.locator("#overview")).toContainText(v);
  const order = await page.locator("[id^='ch']").evaluateAll((els) => els.filter((e) => /^ch\d$/.test(e.id)).map((e) => e.id));
  expect(order).toEqual(["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7"]);
  // Verification is chapter 7: the research hero and first chapters precede any provenance content.
  const y = (id: string) => page.locator(`#${id}`).evaluate((e) => e.getBoundingClientRect().top + scrollY);
  expect(await y("ch1")).toBeLessThan(await y("lineage"));
  expect(await y("ch5")).toBeLessThan(await y("lineage"));
  expect(await y("explorer")).toBeLessThan(await y("evidence"));
});

test("force–time exhibit: defaults, slider, accessible table and export", async ({ page }) => {
  await page.goto("/");
  const readout = page.getByTestId("force-time-readout");
  await expect(readout).toContainText("Mean 20.00 N/kg");
  await expect(readout).toContainText("peak 25.82 N/kg");
  await expect(readout).toContainText("net impulse 2.70 m/s");
  await expect(readout).toContainText("duration 0.265 s");
  const slider = page.getByRole("slider", { name: "Gross mean concentric force, N/kg" });
  await slider.focus();
  await page.keyboard.press("ArrowRight");
  await expect(readout).toContainText("Mean 20.50 N/kg");
  await page.locator("#exhibit-force-time summary").first().click();
  await expect(page.locator("#exhibit-force-time table.pub-table caption")).toContainText("every eighth node of 65");
  await expect(page.locator("#exhibit-force-time .pub-limits")).toContainText("not an observed athlete waveform");
  await expect(page.locator("#exhibit-force-time .pub-page-link")).toHaveAttribute("href", /full_illustrated_manuscript\.pdf#page=3/);
});

test("response exhibit is labelled a synthetic assumption and matches the simulator", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#exhibit-response")).toContainText("Synthetic assumption");
  const readout = page.getByTestId("response-readout");
  await expect(readout).toContainText("H24: -3.73 % (-0.745 N/kg)");
  await expect(readout).toContainText("H72: -1.47 %");
  await expect(page.locator("#exhibit-response .pub-limits")).toContainText("not measured recovery time constants");
});

test("architectures are described, never scored", async ({ page }) => {
  await page.goto("/");
  const banner = page.getByTestId("architecture-banner");
  await expect(banner).toContainText("not");
  await expect(banner).toContainText("compared for predictive accuracy");
  await expect(page.locator("#architecture-progression li")).toHaveCount(9);
  const text = await page.locator("#architecture-progression .sci-prog-list").innerText();
  expect(text).not.toMatch(/NRMSE|\b0\.\d{4}/);
  await expect(page.locator("#architecture-progression")).toContainText("10,796 parameters");
});

test("the paper page leads with the flagship and keeps the retrospective paper as companion", async ({ page, request }) => {
  await page.goto("/paper/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Modeling Countermovement-Jump Recovery");
  await expect(page.locator("#flagship-abstract")).toContainText("0.736270");
  await expect(page.locator("#companion")).toContainText("Companion paper");
  for (const id of ["abstract", "downloads", "sections", "figures", "availability", "cite"]) await expect(page.locator(`#${id}`)).toHaveCount(1);
  for (const [href, pages] of [
    ["/paper/flagship/full_illustrated_manuscript.pdf", 9],
    ["/paper/flagship/academic_review_manuscript.pdf", 16],
    ["/paper/flagship/technical_supplement.pdf", 2],
    ["/paper/full_illustrated_research_manuscript.pdf", 12],
  ] as const) {
    const res = await request.get(href);
    expect(res.status(), href).toBe(200);
    expect((await res.body()).subarray(0, 5).toString()).toBe("%PDF-");
    expect(pages).toBeGreaterThan(0);
  }
});

test("previous deep links still resolve and the site stays noindex", async ({ page }) => {
  for (const url of ["/#explorer", "/#question", "/#world", "/#lineage", "/#lab", "/#evidence", "/#model-atlas", "/?architecture=additive-basis-model&run=2#model-atlas", "/models/#fig-3", "/results/#fig-6", "/methods/#fig-1", "/evidence/"]) {
    await page.goto(url);
    const hash = new URL(page.url()).hash;
    if (hash) await expect(page.locator(hash)).toHaveCount(1);
  }
  await page.goto("/");
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", "noindex, nofollow");
});

test("exhibits stay inside the viewport on a phone", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 320, height: 700 }, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4174/");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator("#exhibit-response").scrollIntoViewIfNeeded();
  await expect(page.locator("#exhibit-response svg.sci-chart")).toBeVisible();
  await context.close();
});
