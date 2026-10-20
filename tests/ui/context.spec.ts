import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import history from "../../src/data/research-history.json";
import context from "../../src/data/context.json";
test("the opening establishes authorship, the setting, measurements and the synthetic boundary", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator(".hero h1")).toContainText("What changes?");
  await expect(page.locator(".hero-byline")).toContainText("Julio Rodriguez");
  await expect(page.locator(".research-cover")).toContainText(
    "One exposure, two outcomes, three horizons",
  );
  await expect(page.locator("#question")).toContainText(
    "Training is the exposure.",
  );
  await expect(page.locator(".setting-context")).toContainText(
    "does not contain athlete observations",
  );
  for (const reference of context.references)
    await expect(
      page.locator(`.context-literature a[href="${reference.href}"]`),
    ).toHaveCount(1);
  for (const [i, expected] of [
    "average force",
    "durations differ",
    "Zero innovation means no change",
  ].entries()) {
    await page.locator(".measurement-tabs button").nth(i).click();
    await expect(page.locator(".measurement-explanation")).toContainText(
      expected,
    );
    await expect(page.locator(".measurement-equation")).toBeVisible();
  }
  await expect(page.locator(".measurement-equation")).toContainText(
    "assessment(h) − pre-exposure baseline",
  );
  await page.locator(".measurement-tabs button").first().focus();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.locator(".measurement-tabs button").nth(1)).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  for (const group of context.exposures) {
    await page
      .locator(".exposure-glossary")
      .getByRole("button", { name: group.label, exact: true })
      .click();
    for (const field of group.fields)
      await expect(
        page.locator(".exposure-glossary code").filter({ hasText: field.name }),
      ).toBeVisible();
  }
});
test("every history decision selects its exact scientific branch while retaining focus", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#lineage");
  for (const [id, note] of Object.entries(history)) {
    const button = page.locator(".history-selector").getByRole("button", {
      name: new RegExp(note.turn.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    });
    await button.click();
    await expect(button).toBeFocused();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(".history-reading h3")).toHaveText(note.turn);
    await expect(page.locator(".history-reading")).toContainText(note.lesson);
    await expect(
      page.locator(`[data-formulation="${id}"] > button`),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(
      page.locator(".desktop-lineage-detail .contract-name"),
    ).toHaveText(id);
  }
});
test("editorial surfaces use solid colour and new exhibits work on touch without overflow", async ({
  browser,
}) => {
  const c = await browser.newContext({
    baseURL: "http://127.0.0.1:4174",
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    reducedMotion: "reduce",
  });
  const page = await c.newPage();
  await page.goto("http://127.0.0.1:4174/");
  await page.locator(".measurement-tabs button").nth(1).tap();
  await expect(page.locator(".measurement-explanation")).toContainText(
    "durations differ",
  );
  await page.locator(".history-selector button").nth(4).tap();
  await expect(page.locator(".history-reading h3")).toHaveText(
    "Repair what is measured",
  );
  for (const width of [320, 375, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `overflow at ${width}`,
    ).toBe(true);
  }
  const surfaces = await page
    .locator(
      "body,.hero,.research-cover,.episode-panel,.metric-lesson,.lab-section",
    )
    .evaluateAll((es) => es.map((e) => getComputedStyle(e).backgroundImage));
  expect(surfaces.every((s) => s === "none")).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    (
      await new AxeBuilder({ page })
        .include("#question")
        .include(".history-reader")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await c.close();
});

test("the response scene loads at its scientific chapter and releases when leaving it", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".instrument-visual canvas")).toHaveCount(0);
  await page.locator(".hero-instrument").scrollIntoViewIfNeeded();
  await expect(page.locator(".instrument-visual canvas")).toBeVisible();
  await page.locator(".hero").scrollIntoViewIfNeeded();
  await expect(page.locator(".instrument-visual canvas")).toHaveCount(0);
});
