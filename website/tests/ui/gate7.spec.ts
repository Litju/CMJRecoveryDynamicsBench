import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("Gate7 routes, mechanics, tour, accessible diagrams and responsive export", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?gate7=M3&repeat=r1#gate7");
  await expect(page.locator(".scroll-journey #gate7")).toHaveCount(0);

  await expect(page.locator(".atlas-detail")).toContainText("M3 / r1");
  for (let i = 0; i < 9; i++)
    for (const r of ["r0", "r1"]) {
      const button = page
        .locator(".route-matrix > div")
        .nth(i)
        .getByRole("button", { name: new RegExp(r) });
      await button.click();
      await expect(button).toHaveAttribute("aria-pressed", "true");
      await expect(page).toHaveURL(new RegExp(`gate7=M${i}&repeat=${r}`));
    }
  await page.locator("#concentric-duration").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#native-force")).toContainText("2.46000 m/s");
  await page.locator("#native-force summary").click();
  await expect(page.locator("#native-force tbody tr")).toHaveCount(41);
  const downloadPromise = page.waitForEvent("download");
  await page
    .locator("#native-force")
    .getByRole("button", { name: "Export SVG" })
    .click();
  expect((await downloadPromise).suggestedFilename()).toBe("native-force.svg");
  await page
    .locator(".atlas-tour")
    .getByRole("button", { name: "Next", exact: true })
    .click();
  await expect(page.locator(".atlas-tour h2")).toHaveText("Eight formulations");
  expect(
    (
      await new AxeBuilder({ page })
        .include(".atlas-wrap")
        .include(".atlas-tour")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.locator("#native-force summary").click();
  await page
    .locator("#gate7")
    .screenshot({ style: ".site-header, .skip-link { visibility: hidden !important; }", path: "docs/atlas/desktop-models.png" });
  await page
    .locator("#native-mechanics")
    .screenshot({ style: ".site-header, .skip-link { visibility: hidden !important; }", path: "docs/atlas/desktop-mechanics.png" });
  await page
    .locator("#gate7-evidence")
    .screenshot({ style: ".site-header, .skip-link { visibility: hidden !important; }", path: "docs/atlas/desktop-evidence.png" });
  await page
    .locator("#intro")
    .screenshot({ style: ".site-header, .skip-link { visibility: hidden !important; }", path: "docs/atlas/desktop-hero.png" });
  for (const width of [768, 390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `width ${width}`,
    ).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .locator("#gate7")
    .screenshot({ style: ".site-header, .skip-link { visibility: hidden !important; }", path: "docs/atlas/mobile-models.png" });
  await page
    .locator("#native-mechanics")
    .screenshot({ style: ".site-header, .skip-link { visibility: hidden !important; }", path: "docs/atlas/mobile-mechanics.png" });
});
