import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { OrthographicCamera, Vector3 } from "three";
import fixture from "../../src/data/results.json";
import { plotTheme } from "../../src/lib/plot-theme.mjs";
const ids = [
  "zero_innovation",
  "training_constant",
  "ridge_full",
  "structured_full",
] as const;
async function projectedPoint(
  page: Page,
  selector: string,
  point: [number, number, number],
) {
  const box = (await page.locator(selector).boundingBox())!;
  const camera = new OrthographicCamera(
    -box.width / 2,
    box.width / 2,
    box.height / 2,
    -box.height / 2,
    0.1,
    100,
  );
  camera.position.set(0, 5, 14);
  camera.lookAt(0, 1, 0);
  camera.zoom = Math.min(box.width / 12.5, box.height / 8.5);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
  const p = new Vector3(...point).project(camera);
  return {
    x: box.x + ((p.x + 1) * box.width) / 2,
    y: box.y + ((1 - p.y) * box.height) / 2,
  };
}
test("SVG and Recharts use the same specimen palette, model colours and square tooltips", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#explorer");
  await expect(
    page.locator(".chart .recharts-cartesian-grid line").first(),
  ).toHaveAttribute("stroke", plotTheme.grid);
  await expect(page.locator(".interval-plot line").nth(1)).toHaveAttribute(
    "stroke",
    plotTheme.ridge,
  );
  await page.locator(".model-option").nth(3).click();
  await expect(page.locator(".interval-plot line").nth(1)).toHaveAttribute(
    "stroke",
    plotTheme.structured,
  );
  await page.locator(".chart .recharts-line-dot").last().hover();
  await expect(page.locator(".chart .recharts-default-tooltip")).toBeVisible();
  await expect(page.locator(".chart .recharts-default-tooltip")).toHaveCSS(
    "background-color",
    "rgb(33, 52, 62)",
  );
  await expect(page.locator(".chart .recharts-default-tooltip")).toHaveCSS(
    "border-radius",
    "0px",
  );
  await expect(
    page.locator(".lab-chart .recharts-cartesian-grid line").first(),
  ).toHaveAttribute("stroke", plotTheme.grid);
});
test("the 3D matrix preserves all 96 sourced values and links selection to existing controls", async ({
  page,
}) => {
  await page.goto("/#explorer");
  await page
    .getByRole("button", { name: "3D comparison", exact: true })
    .click();
  await expect(page.locator(".benchmark-canvas canvas")).toBeVisible();
  await page.locator(".scene-matrix summary").click();
  for (const root of ["mean", "A", "B", "C"]) {
    await page.selectOption("#root-select", root);
    const actual = await page
      .locator(".scene-matrix button[data-cell]")
      .evaluateAll((bs) =>
        bs.map((b) => ({
          key: b.getAttribute("data-cell"),
          value: b.textContent,
        })),
      );
    expect(actual).toHaveLength(24);
    const roots = fixture.roots.filter((r) => root === "mean" || r.id === root);
    for (const item of actual) {
      const [id, h, o] = item.key!.split("/");
      const key = `H${h}/${o === "force" ? "relative_peak_mean_force_innovation" : "net_impulse_innovation"}`;
      const values = roots.map(
        (r) =>
          r.models[id as (typeof ids)[number]].cells.find(
            (c) => c.cell === key,
          )!.nrmse,
      );
      expect(item.value).toBe(
        (values.reduce((a, b) => a + b) / values.length).toFixed(6),
      );
    }
    await page
      .getByRole("button", { name: "Constant H48 impulse", exact: true })
      .click();
    await expect(page.locator(".model-option").nth(1)).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(
      page.getByRole("button", { name: "H48", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(
      page.getByRole("button", { name: "Net impulse", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByTestId("scene-cell-score")).toHaveText(
      Number(
        actual.find((x) => x.key === "training_constant/48/impulse")!.value,
      ).toFixed(6),
    );
  }
  expect(
    (
      await new AxeBuilder({ page })
        .include("#explorer")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page
    .getByRole("button", { name: "2D horizon plot", exact: true })
    .click();
  await expect(page.locator(".benchmark-canvas canvas")).toHaveCount(0);
  await expect(page.locator(".chart")).toBeVisible();
});
test("real 3D bars can be picked, camera views change rendering, and lost graphics recover to exact data", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/#explorer");
  await page
    .getByRole("button", { name: "3D comparison", exact: true })
    .click();
  const chart = page.locator(".benchmark-3d");
  const canvas = page.locator(".benchmark-canvas");
  await expect(canvas.locator("canvas")).toBeVisible();
  await chart.getByRole("button", { name: "Front view", exact: true }).click();
  await canvas.scrollIntoViewIfNeeded();
  const v =
    fixture.roots.reduce(
      (s, r) =>
        s +
        r.models.structured_full.cells.find(
          (c) => c.cell === "H48/net_impulse_innovation",
        )!.nrmse,
      0,
    ) / 3;
  const point = await projectedPoint(page, ".benchmark-canvas", [
    0.6,
    v / 2,
    2.1,
  ]);
  await page.mouse.click(point.x, point.y);
  await expect(page.locator(".model-option").last()).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByTestId("cell-score")).toHaveText(v.toFixed(4));
  const front = await canvas.screenshot();
  await chart
    .getByRole("button", { name: "Overhead view", exact: true })
    .click();
  const overhead = await canvas.screenshot();
  expect(front.equals(overhead)).toBe(false);
  await chart
    .getByRole("button", { name: "Enable drag rotation", exact: true })
    .click();
  await expect(canvas.locator("canvas")).toHaveCSS("touch-action", "none");
  await chart
    .getByRole("button", { name: "Disable drag rotation", exact: true })
    .click();
  await expect(canvas.locator("canvas")).toHaveCSS("touch-action", "pan-y");
  await canvas.locator("canvas").evaluate((c) => {
    const gl = (c as HTMLCanvasElement).getContext("webgl2")!;
    gl.getExtension("WEBGL_lose_context")!.loseContext();
  });
  await expect(canvas.locator("canvas")).toHaveCount(0);
  await expect(chart.locator(".benchmark-3d-fallback")).toContainText(
    "graphics context was lost",
  );
  await expect(chart.locator(".scene-matrix")).toHaveAttribute("open", "");
  expect(errors).toEqual([]);
});
test("response curves have real camera, scale, drag and elapsed-time picking controls", async ({
  page,
}) => {
  await page.goto("/#remaining");
  const figure = page.locator(".hero-instrument");
  await figure.scrollIntoViewIfNeeded();
  const canvas = page.locator(".instrument-visual");
  await expect(canvas.locator("canvas")).toBeVisible();
  await figure.getByRole("button", { name: "Front view", exact: true }).focus();
  await page.keyboard.press("Enter");
  await canvas.scrollIntoViewIfNeeded();
  const point = await projectedPoint(page, ".instrument-visual", [
    0,
    0.3 * Math.exp(-1) * 3,
    1.6,
  ]);
  await page.mouse.click(point.x, point.y);
  await expect(page.locator("#hero-time")).toHaveValue("84");
  await expect(page.getByTestId("hero-response")).toHaveText(
    (0.7 * Math.exp(-84 / 24) + 0.3 * Math.exp(-1)).toFixed(4),
  );
  await figure.getByRole("slider", { name: "3D scene scale" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(
    figure.getByRole("slider", { name: "3D scene scale" }),
  ).toHaveValue("43");
  await figure
    .getByRole("button", { name: "Enable drag rotation", exact: true })
    .click();
  const box = (await canvas.boundingBox())!;
  const before = await canvas.screenshot();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 90,
    box.y + box.height / 2 + 35,
    { steps: 8 },
  );
  await page.mouse.up();
  expect(before.equals(await canvas.screenshot())).toBe(false);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(canvas.locator("canvas")).toHaveCount(0);
  await expect(page.getByTestId("instrument-fallback")).toBeVisible();
});
test("3D remains usable with reduced motion, missing WebGL, mobile touch and no page overflow", async ({
  browser,
}) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4173/#explorer");
  await page.getByRole("button", { name: "3D comparison", exact: true }).tap();
  await expect(page.locator(".benchmark-canvas canvas")).toHaveCount(0);
  await expect(page.locator(".benchmark-3d-fallback")).toContainText(
    "Reduced motion",
  );
  await page
    .getByRole("button", { name: "Ridge H72 force", exact: true })
    .tap();
  await expect(
    page.getByRole("button", { name: "H72", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  for (const width of [320, 375, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `overflow at ${width}`,
    ).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.locator(".benchmark-canvas").scrollIntoViewIfNeeded();
  await expect(page.locator(".benchmark-canvas canvas")).toBeVisible();
  await page
    .locator(".benchmark-3d")
    .getByRole("button", { name: "Front view", exact: true })
    .tap();
  await expect(page.locator(".benchmark-canvas canvas")).toHaveCSS(
    "touch-action",
    "pan-y",
  );
  await page.locator(".scene-matrix summary").tap();
  await page
    .getByRole("button", { name: "Structured H48 impulse", exact: true })
    .tap();
  await expect(page.locator(".model-option").last()).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(
    (
      await new AxeBuilder({ page })
        .include("#explorer")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await context.close();
  const unavailable = await browser.newContext();
  await unavailable.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...args: unknown[]
    ) {
      if (type === "webgl2" || type === "webgl") return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  const fallback = await unavailable.newPage();
  await fallback.goto("http://127.0.0.1:4173/#explorer");
  await fallback
    .getByRole("button", { name: "3D comparison", exact: true })
    .click();
  await expect(fallback.locator(".benchmark-3d-fallback")).toContainText(
    "WebGL is unavailable",
  );
  await expect(fallback.locator(".scene-matrix button[data-cell]")).toHaveCount(
    24,
  );
  await unavailable.close();
});
