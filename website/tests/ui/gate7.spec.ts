import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("Gate7 routes, mechanics, tour, accessible diagrams and responsive export", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?gate7=M3&repeat=r1#gate7");
  await expect(page.locator(".scroll-journey #model-atlas")).toHaveCount(0);

  await expect(page.locator(".atlas-detail")).toContainText("Repeat 2");
  await expect(page.locator(".atlas-detail h3")).toHaveText("History encoder");
  await expect(page.locator(".atlas-wrap")).toHaveCSS(
    "background-color",
    "rgba(0, 0, 0, 0)",
  );
  await expect(page.locator(".atlas-panel").first()).toHaveCSS(
    "background-color",
    "rgb(255, 253, 247)",
  );
  await expect(page.locator(".atlas-wrap .eyebrow").first()).toHaveCSS(
    "color",
    "rgb(40, 84, 184)",
  );
  await expect(page.locator(".atlas-wrap button").first()).toHaveCSS(
    "border-radius",
    "0px",
  );
  expect(await page.locator("body").innerText()).not.toMatch(
    /Gate7|GATE7|RES-\d+/,
  );
  for (let i = 0; i < 9; i++)
    for (const r of ["r0", "r1"]) {
      const button = page
        .locator(".route-matrix > div")
        .nth(i)
        .getByRole("button", {
          name: new RegExp(`Repeat ${Number(r.slice(1)) + 1}`),
        });
      await button.click();
      await expect(button).toHaveAttribute("aria-pressed", "true");
      await expect(page).toHaveURL(
        new RegExp(`architecture=.*&run=${Number(r.slice(1)) + 1}#model-atlas`),
      );
    }
  await page.reload();
  await expect(page.locator(".atlas-detail h3")).toHaveText(
    "Additive basis model",
  );
  await expect(page.locator(".atlas-detail > .eyebrow")).toContainText(
    "Repeat 2",
  );
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
  await page.locator("#model-atlas").screenshot({
    style: ".site-header, .skip-link { visibility: hidden !important; }",
    path: "docs/atlas/desktop-models.png",
  });
  await page.locator("#native-mechanics").screenshot({
    style: ".site-header, .skip-link { visibility: hidden !important; }",
    path: "docs/atlas/desktop-mechanics.png",
  });
  await page.locator("#research-evidence").screenshot({
    style: ".site-header, .skip-link { visibility: hidden !important; }",
    path: "docs/atlas/desktop-evidence.png",
  });
  await page.locator("#intro").screenshot({
    style: ".site-header, .skip-link { visibility: hidden !important; }",
    path: "docs/atlas/desktop-hero.png",
  });
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
  await page.locator("#model-atlas").screenshot({
    style: ".site-header, .skip-link { visibility: hidden !important; }",
    path: "docs/atlas/mobile-models.png",
  });
  await page.locator("#native-mechanics").screenshot({
    style: ".site-header, .skip-link { visibility: hidden !important; }",
    path: "docs/atlas/mobile-mechanics.png",
  });
});
