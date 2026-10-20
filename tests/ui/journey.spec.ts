import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { chapters, journeyBars } from "../../src/lib/journey";
import fixture from "../../src/data/results.json";
test("the persistent 3D stage follows every chapter and scroll changes its actual rendering", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/");
    const stage = page.locator(".journey-stage");
    const canvas = stage.locator("canvas");
    await expect(canvas).toBeVisible();
    for (const chapter of chapters) {
        await page.locator(`#${chapter.id}`).evaluate((e) => e.scrollIntoView({ block: "start", behavior: "instant" }));
        await expect(stage).toHaveAttribute("data-chapter", chapter.id);
        await expect(stage.locator('a[aria-current="step"]')).toHaveAttribute("href", `#${chapter.id}`);
        await expect(stage.locator("h2")).toHaveText(chapter.title);
        const box = (await stage.boundingBox())!;
        expect(box.y).toBeGreaterThanOrEqual(79);
        expect(box.y).toBeLessThan(100);
    }
    await page.locator("#world").evaluate((e) => e.scrollIntoView({ block: "start", behavior: "instant" }));
    await expect(stage).toHaveAttribute("data-chapter", "world");
    const initial = await stage.getAttribute("data-progress");
    const before = await canvas.screenshot();
    await page.evaluate(() => scrollBy(0, 550));
    await expect(stage).not.toHaveAttribute("data-progress", initial!);
    expect((await canvas.screenshot()).equals(before)).toBe(false);
    await stage.getByRole("button", { name: "Pause motion", exact: true }).click();
    const paused = await canvas.screenshot();
    await page.evaluate(() => scrollBy(0, 350));
    await page.waitForTimeout(100);
    expect((await canvas.screenshot()).equals(paused)).toBe(true);
    await stage.getByRole("button", { name: "Resume motion", exact: true }).click();
    await stage.getByRole("button", { name: "Rotate scene", exact: true }).click();
    await expect(canvas).toHaveCSS("touch-action", "none");
    await stage.getByRole("button", { name: "Release scene", exact: true }).click();
    await expect(canvas).toHaveCSS("touch-action", "pan-y");
    expect(errors).toEqual([]);
});
test("all scientific figures use light surfaces and readable native alternatives", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    await expect(page.locator(".journey-viewport canvas")).toHaveCount(0);
    const figures = page.locator(".research-cover,.episode-panel,.layer-exhibit,#experiment,#explorer,.chart,.lab-chart,.lab-section,.lab-panel,.metric-lesson,.interval-plot,.hero-instrument,.journey-stage");
    const surfaces = await figures.evaluateAll((els) => els.map((el) => {
        const s = getComputedStyle(el);
        const rgb = s.backgroundColor.match(/\d+/g)?.map(Number) || [];
        return { name: el.className || el.id, rgb, image: s.backgroundImage };
    }));
    for (const surface of surfaces) {
        expect(surface.image, surface.name).toBe("none");
        expect(surface.rgb.slice(0, 3).every((v) => v >= 230), surface.name).toBe(true);
    }
    await page.locator('.journey-index a[href="#explorer"]').click();
    await expect(page.locator(".journey-stage")).toHaveAttribute("data-chapter", "explorer");
    for (const model of journeyBars) {
        const values = fixture.roots.map((r) => r.models[model.id].cells.find((c) => c.cell === "H24/relative_peak_mean_force_innovation")!.nrmse);
        expect(model.value).toBe(values.reduce((a, b) => a + b, 0) / 3);
        await expect(page.locator(".journey-fallback")).toContainText(model.value.toFixed(4));
    }
    expect((await new AxeBuilder({ page }).include(".journey-stage").withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
});
test("mobile keeps chapter navigation, touch scrolling and controls reachable", async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: "reduce" });
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:4173/");
    for (const id of ["question", "world", "lineage", "explorer", "lab", "evidence"]) {
        await page.locator(`.journey-index a[href="#${id}"]`).tap();
        await expect(page.locator(".journey-stage")).toHaveAttribute("data-chapter", id);
        const box = (await page.locator(`#${id}`).boundingBox())!;
        const stage = (await page.locator(".journey-stage").boundingBox())!;
        expect(box.y).toBeGreaterThanOrEqual(stage.y + stage.height);
    }
    await page.locator('.journey-index a[href="#explorer"]').tap();
    await page.locator(".model-option").nth(3).tap();
    await expect(page.locator(".model-option").nth(3)).toHaveAttribute("aria-pressed", "true");
    for (const width of [320, 375, 768, 1024, 1440]) {
        await page.setViewportSize({ width, height: 844 });
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await page.locator('.journey-index a[href="#lineage"]').tap();
    const stage = page.locator(".journey-stage");
    await expect(stage).toHaveAttribute("data-chapter", "lineage");
    await expect(stage.locator("canvas")).toBeVisible();
    const heading = (await stage.locator("h2").boundingBox())!;
    const controls = (await stage.locator(".journey-interactions").boundingBox())!;
    const navigation = (await stage.locator(".journey-index").boundingBox())!;
    const graphic = (await stage.locator(".journey-viewport").boundingBox())!;
    expect(heading.y + heading.height).toBeLessThanOrEqual(controls.y + 1);
    expect(controls.y + controls.height).toBeLessThanOrEqual(navigation.y + 1);
    expect(graphic.x + graphic.width).toBeLessThanOrEqual(390);
    await page.setViewportSize({ width: 844, height: 390 });
    await page.locator('.journey-index a[href="#evidence"]').tap();
    await expect(stage).toHaveAttribute("data-chapter", "evidence");
    const landscapeStage = (await stage.boundingBox())!;
    expect(landscapeStage.y + landscapeStage.height).toBeLessThanOrEqual(250);
    expect((await page.locator("#evidence").boundingBox())!.y).toBeGreaterThanOrEqual(landscapeStage.y + landscapeStage.height);
    await context.close();
});

test("picking a sourced bar in the persistent stage selects its actual benchmark model", async ({ page }) => {
  const { OrthographicCamera, Vector3 } = await import("three");
  await page.goto("/#explorer");
  const stage = page.locator(".journey-stage");
  await expect(stage).toHaveAttribute("data-chapter", "explorer");
  const canvas = stage.locator("canvas");
  await expect(canvas).toBeVisible();
  await page.selectOption("#root-select", "B");
  await page.getByRole("button", { name: "H72", exact: true }).click();
  await page.getByRole("button", { name: "Net impulse", exact: true }).click();
  await page.getByRole("button", { name: "RMSE", exact: true }).click();
  const p = Number(await stage.getAttribute("data-progress"));
  await stage.getByRole("button", { name: "Pause motion", exact: true }).click();
  const box = (await canvas.boundingBox())!;
  const camera = new OrthographicCamera(-box.width / 2, box.width / 2, box.height / 2, -box.height / 2, 0.1, 100);
  camera.position.set(8 + p * 5, 7 + p * 2, 14 - p * 4);
  camera.lookAt(0, 1, 0);
  camera.zoom = Math.min(box.width / 12.5, box.height / 8.5) * 45 / 42;
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
  const point = new Vector3(3, journeyBars[3].value / 2, 0.5).project(camera);
  await page.mouse.click(box.x + (point.x + 1) * box.width / 2, box.y + (1 - point.y) * box.height / 2);
  await expect(page.locator('#explorer [data-model-id="structured_full"]')).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#root-select")).toHaveValue("mean");
  await expect(page.getByRole("button", { name: "H24", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Force", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("cell-score")).toHaveText(journeyBars[3].value.toFixed(4));
  await expect(page.locator(".axis-unit")).toHaveText("NRMSE · UNITLESS");
});
