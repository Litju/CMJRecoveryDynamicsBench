import { test, expect, type Page } from "@playwright/test";
async function range(page: Page, selector: string, value: string) {
  await page.locator(selector).evaluate((input, value) => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }, value);
}
import AxeBuilder from "@axe-core/playwright";
import fixture from "../../src/data/results.json";
const ids = [
  "zero_innovation",
  "training_constant",
  "ridge_full",
  "structured_full",
] as const;
test("all 96 model/root/horizon/outcome combinations show exact sourced values", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    await page.locator(".model-option").nth(i).click();
    for (const root of ["mean", "A", "B", "C"]) {
      await page.selectOption("#root-select", root);
      const roots = fixture.roots.filter(
        (r) => root === "mean" || r.id === root,
      );
      const aggregate =
        roots.reduce((s, r) => s + r.models[id].mean_six_cell_nrmse, 0) /
        roots.length;
      await expect(page.getByTestId("aggregate-score")).toHaveText(
        aggregate.toFixed(4),
      );
      for (const h of [24, 48, 72]) {
        await page.getByRole("button", { name: `H${h}`, exact: true }).click();
        for (const outcome of ["force", "impulse"]) {
          await page
            .getByRole("button", {
              name: outcome === "force" ? "Force" : "Net impulse",
              exact: true,
            })
            .click();
          const key = `H${h}/${outcome === "force" ? "relative_peak_mean_force_innovation" : "net_impulse_innovation"}`;
          const values = roots.map(
            (r) => r.models[id].cells.find((c) => c.cell === key)!,
          );
          const nrmse = values.reduce((s, v) => s + v.nrmse, 0) / roots.length;
          const rmse = values.reduce((s, v) => s + v.rmse, 0) / roots.length;
          await expect(page.getByTestId("cell-score")).toHaveText(
            nrmse.toFixed(4),
          );
          await expect(page.getByTestId("cell-rmse")).toContainText(
            rmse.toFixed(4),
          );
          await expect(page.getByTestId("cell-rmse")).toContainText(
            outcome === "force" ? "N/kg" : "m/s",
          );
          await expect(page.locator(".active-row")).toContainText(`H${h}`);
        }
      }
    }
  }
  await page.getByRole("button", { name: "RMSE", exact: true }).click();
  await expect(page.locator(".axis-unit")).toHaveText("RMSE · m/s");
  await page.selectOption("#compare-select", "structured_full");
  await expect(page.locator(".comparison-note")).toContainText("0.0000");
  await expect(page.locator(".uncertainty-content tbody tr")).toHaveCount(1);
});
test("ledger selection, root intervals, keyboard controls and download provenance", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to research" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await page.locator(".cell-table tbody button").last().click();
  await expect(
    page.getByRole("button", { name: "H72", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(
    page.getByRole("button", { name: "Net impulse", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.selectOption("#root-select", "A");
  await expect(page.locator(".uncertainty-content")).toContainText(
    "[0.7280, 0.7462]",
  );
  await expect(page.locator(".uncertainty-content")).toContainText(
    "[-1.7522, -1.6450]",
  );
  await page.locator("#root-select").focus();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page.locator("#root-select")).toHaveValue("B");
  const download = await page.request.get("/data/results.json");
  expect(download.status()).toBe(200);
  expect((await download.json()).provenance.commit).toBe(
    fixture.provenance.commit,
  );
  await page.locator(".provenance summary").click();
  await expect(page.locator(".provenance-content")).toContainText(
    fixture.provenance.resultsSha256,
  );
});
test("lab sliders, time keyboard, play/pause and reset follow the equation", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await range(page, "#fast-amplitude", "1.2");
  await range(page, "#slow-amplitude", "0.6");
  await range(page, "#lab-time", "84");
  await expect(page.getByTestId("lab-value")).toHaveText(
    (1.2 * Math.exp(-84 / 24) + 0.6 * Math.exp(-1)).toFixed(4),
  );
  await page.locator("#lab-time").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#lab-time")).toHaveValue("85");
  await page.getByRole("button", { name: "Play time" }).click();
  await expect(page.locator("#lab-time")).not.toHaveValue("85");
  await page.getByRole("button", { name: "Pause time" }).click();
  await expect(page.getByRole("button", { name: "Play time" })).toHaveAttribute(
    "aria-pressed",
    "false",
  );
  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await expect(page.locator("#fast-amplitude")).toHaveValue("0.7");
  await expect(page.locator("#slow-amplitude")).toHaveValue("0.3");
  await expect(page.locator("#lab-time")).toHaveValue("24");
  await expect(page.getByTestId("lab-value")).toHaveText(
    (0.7 * Math.exp(-1) + 0.3 * Math.exp(-24 / 84)).toFixed(4),
  );
});
test("desktop accessibility, 3D time scrub and no runtime errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.locator(".instrument-visual canvas")).toBeVisible();
  await range(page, "#hero-time", "72");
  await expect(page.locator(".instrument-scrub output")).toContainText("072");
  await expect(page.locator("#hero-time")).toHaveAttribute(
    "aria-valuetext",
    "72 illustrative hours",
  );
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
  expect(errors).toEqual([]);
  await page.screenshot({ path: "docs/desktop.png", fullPage: true });
});
test("mobile and reduced-motion fallback remain accessible without overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const scripts: string[] = [];
  page.on("request", (r) => {
    if (r.resourceType() === "script") scripts.push(r.url());
  });
  await page.goto("/");
  await expect(page.getByTestId("instrument-fallback")).toBeVisible();
  await expect(page.locator(".instrument-visual canvas")).toHaveCount(0);
  await page.getByRole("link", { name: "Explore benchmark" }).click();
  await page.getByRole("button", { name: "Net impulse", exact: true }).click();
  await expect(page.getByTestId("cell-rmse")).toContainText("m/s");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: "docs/mobile.png", fullPage: true });
  for (const width of [320, 375, 768, 1024]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `No overflow at ${width}px`,
    ).toBe(true);
  }
});
test("WebGL unavailable uses the 2D instrument and keeps research interactive", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const get = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...args: unknown[]
    ) {
      if (type === "webgl" || type === "webgl2") return null;
      return Reflect.apply(get, this, [type, ...args]);
    } as typeof get;
  });
  await page.goto("/");
  await expect(page.getByTestId("instrument-fallback")).toBeVisible();
  await page.locator(".model-option").first().click();
  await expect(page.getByTestId("aggregate-score")).toHaveText("2.4307");
});
