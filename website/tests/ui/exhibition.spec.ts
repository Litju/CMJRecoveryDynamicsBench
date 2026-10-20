import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import exhibit from "../../src/data/exhibition.json";
import fixture from "../../src/data/results.json";
import methods from "../../src/data/methods.json";
import nodes from "../../src/data/lineage.json";
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
test("episode boundary, all events and layers, keyboard, playback and reset", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#world");
  const scene = page.locator(".episode-scene");
  for (const event of exhibit.events) {
    await page.locator(`[data-event="${event.id}"]`).click();
    await expect(page.locator(".episode-caption h3")).toHaveText(event.title);
    await expect(scene).toHaveAttribute("data-perspective", "model");
    await expect(page.locator(".episode-boundary")).toContainText(
      "future outcomes are withheld",
    );
    await expect(page.locator(`[data-event="${event.id}"]`)).toHaveAttribute(
      "data-predictor",
      String(event.available),
    );
  }
  await page
    .getByRole("button", { name: "Later observer", exact: true })
    .click();
  await expect(scene).toHaveAttribute("data-perspective", "observer");
  await expect(scene.locator("svg")).toContainText("✓");
  await expect(page.locator(".episode-boundary")).toContainText(
    "remain excluded",
  );
  for (const layer of exhibit.layers) {
    await page
      .locator(".layer-choices")
      .getByRole("button", { name: new RegExp(layer.label) })
      .click();
    await expect(page.locator(".layer-detail h3")).toHaveText(layer.title);
    await expect(scene).toHaveAttribute("data-layer", layer.id);
  }
  await page
    .locator(".layer-choices")
    .getByRole("button", { name: /Observation/ })
    .click();
  await page
    .getByRole("button", { name: "Net-impulse area", exact: true })
    .click();
  await expect(page.locator(".measurement-lens")).toContainText("J/m =");
  await page.getByRole("button", { name: "Mean force", exact: true }).click();
  await expect(page.locator(".measurement-lens")).toContainText(
    "divided by phase duration",
  );
  await page.locator("#episode-time").focus();
  await page.keyboard.press("Home");
  await expect(page.locator("#episode-time")).toHaveValue("0");
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#episode-time")).toHaveValue("1");
  await page.getByRole("button", { name: "Play episode", exact: true }).click();
  await expect(page.locator("#episode-time")).not.toHaveValue("1");
  await page
    .getByRole("button", { name: "Pause episode", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Reset episode", exact: true })
    .click();
  await expect(page.locator("#episode-time")).toHaveValue("2");
  await expect(scene).toHaveAttribute("data-layer", "predictor");
  await expect(scene).toHaveAttribute("data-perspective", "model");
  await page
    .getByText("Methods & evidence · the complete predictor budget", {
      exact: true,
    })
    .click();
  await expect(page.locator(".feature-budget article")).toHaveCount(5);
  expect(
    (
      await new AxeBuilder({ page })
        .include("#world")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("real-cell teaching arithmetic, all diagnostic configurations and frozen selection", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#metric-lesson");
  const lesson = page.locator(".metric-lesson");
  const ids = [
    "zero_innovation",
    "training_constant",
    "ridge_full",
    "structured_full",
  ] as const;
  for (const id of ids) {
    await lesson.locator("select").first().selectOption(id);
    for (const root of fixture.roots) {
      await lesson.locator("select").last().selectOption(root.id);
      for (let i = 0; i < 6; i++) {
        await lesson.locator(".six-cells button").nth(i).click();
        const cell = root.models[id].cells[i];
        await expect(page.getByTestId("lesson-rmse")).toHaveText(
          cell.rmse.toFixed(6),
        );
        await expect(page.getByTestId("lesson-sd")).toHaveText(
          cell.truth_population_sd.toFixed(6),
        );
        await expect(page.getByTestId("lesson-nrmse")).toHaveText(
          cell.nrmse.toFixed(6),
        );
      }
      await expect(page.getByTestId("lesson-aggregate")).toHaveText(
        root.models[id].mean_six_cell_nrmse.toFixed(6),
      );
    }
  }
  await lesson.locator("summary").click();
  await expect(lesson).toContainText("at least 1");
  for (const id of [
    "ridge_no_prior_history",
    "ridge_no_current_exposure",
    "ridge_no_participant_context",
    "structured_no_prior_history",
  ] as const) {
    await page.selectOption("#ablation-select", id);
    const base = id.startsWith("ridge") ? "ridge_full" : "structured_full";
    await expect(page.getByTestId("ablation-delta")).toHaveText(
      "+" +
        (
          methods.variants[id].root_mean_nrmse -
          methods.variants[base].root_mean_nrmse
        ).toFixed(6),
    );
  }
  for (const n of [24, 48, 96] as const) {
    await page.getByRole("button", { name: `${n} camps`, exact: true }).click();
    for (const id of ["ridge", "structured", "training_constant"] as const)
      await expect(page.getByTestId(`sample-${id}`)).toHaveText(
        methods.variants[`${id}_n${n}`].root_mean_nrmse.toFixed(6),
      );
  }
  await page
    .getByText(
      "Methods & evidence · splits, transformations and model selection",
      { exact: true },
    )
    .click();
  await expect(page.locator(".study-methods tbody tr")).toHaveCount(6);
  await expect(page.locator(".study-methods tbody tr")).toContainText([
    "0.01",
    "0.01",
    "0.01",
    "0.01",
    "0.01",
    "0.01",
  ]);
  const download = await page.request.get("/data/methods.json");
  expect(await download.json()).toEqual(methods);
  await page.locator(".protocol-raw summary").click();
  expect(
    JSON.parse((await page.locator(".protocol-raw pre").textContent())!),
  ).toEqual(fixture.protocol);
});

test("lineage deep links, browser history, all methods sheets and invalid query fallback", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?formulation=threshold_response_recovery#lineage");
  await expect(
    page.locator(".desktop-lineage-detail .contract-name"),
  ).toHaveText("threshold_response_recovery");
  for (const node of nodes) {
    await page.locator(`[data-formulation="${node.id}"] > button`).click();
    await expect(page).toHaveURL(new RegExp(`formulation=${node.id}#lineage`));
    const panel = page.locator(".desktop-lineage-detail");
    await panel.locator(".formulation-methods summary").click();
    await expect(panel.locator(".formulation-methods")).toContainText(
      "World / dynamics family",
    );
    await expect(panel.locator(".formulation-methods")).toContainText(
      "Observation law",
    );
  }
  await page.goBack();
  await expect(
    page.locator(".desktop-lineage-detail .contract-name"),
  ).toHaveText("threshold_response_recovery");
  await page.reload();
  await expect(
    page.locator(".desktop-lineage-detail .contract-name"),
  ).toHaveText("threshold_response_recovery");
  await page.goto("/?formulation=unknown#lineage");
  await expect(
    page.locator(".desktop-lineage-detail .contract-name"),
  ).toHaveText("fixed_mode_discrepancy_recovery");
  await page.goto("/#world");
  await page.locator(".world-cards a").nth(1).click();
  await expect(
    page.locator(".desktop-lineage-detail .contract-name"),
  ).toHaveText("correlated_exposure_recovery");
});

test("signed lab scenarios, slope and area, reset, hero modes and reduced-motion transitions", async ({
  page,
}) => {
  await page.goto("/#lab");
  await page
    .getByRole("button", { name: "Opposing modes", exact: true })
    .click();
  await range(page, "#lab-time", "48");
  const a = -0.7,
    b = 0.3,
    t = 48;
  await expect(page.getByTestId("lab-value")).toHaveText(
    (a * Math.exp(-t / 24) + b * Math.exp(-t / 84)).toFixed(4),
  );
  await expect(page.getByTestId("lab-slope")).toHaveText(
    ((-a / 24) * Math.exp(-t / 24) - (b / 84) * Math.exp(-t / 84)).toFixed(6),
  );
  await expect(page.getByTestId("lab-integral")).toHaveText(
    (
      24 * a * (1 - Math.exp(-t / 24)) +
      84 * b * (1 - Math.exp(-t / 84))
    ).toFixed(4),
  );
  for (const name of ["Rate of change", "Accumulated area", "Response"]) {
    await page.getByRole("button", { name, exact: true }).click();
    await expect(
      page.getByRole("button", { name, exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    const value =
      name === "Response"
        ? a * Math.exp(-t / 24) + b * Math.exp(-t / 84)
        : name === "Rate of change"
          ? (-a / 24) * Math.exp(-t / 24) - (b / 84) * Math.exp(-t / 84)
          : 24 * a * (1 - Math.exp(-t / 24)) + 84 * b * (1 - Math.exp(-t / 84));
    await expect(page.getByTestId("lab-chart-value")).toHaveText(
      value.toFixed(name === "Rate of change" ? 6 : 4),
    );
  }
  await page
    .getByRole("button", { name: "Cancel at origin", exact: true })
    .click();
  await range(page, "#lab-time", "0");
  await expect(page.getByTestId("lab-value")).toHaveText("0.0000");
  await page.getByRole("button", { name: "Play time", exact: true }).click();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(
    page.getByRole("button", { name: "Play time", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await expect(page.locator("#fast-amplitude")).toHaveValue("0.7");
  await expect(page.locator("#lab-time")).toHaveValue("24");
  await page.getByRole("button", { name: "24 h only", exact: true }).click();
  await range(page, "#hero-time", "24");
  await expect(page.getByTestId("hero-response")).toHaveText(
    (0.7 * Math.exp(-1)).toFixed(4),
  );
  await page.getByRole("button", { name: "84 h only", exact: true }).click();
  await expect(page.getByTestId("hero-response")).toHaveText(
    (0.3 * Math.exp(-24 / 84)).toFixed(4),
  );
  await expect(page.locator(".instrument-visual canvas")).toHaveCount(0);
});

test("expanded scientific methods and proposed roadmap are accessible on desktop", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.locator("details").evaluateAll((ds) =>
    ds.forEach((d) => {
      if (d instanceof HTMLDetailsElement) d.open = true;
    }),
  );
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await expect(page.locator(".evidence-ladder .evidence-rung")).toHaveCount(5);
  await expect(page.locator(".roadmap")).toContainText("PROPOSED WORK");
  await expect(page.locator(".quick-route li")).toHaveCount(4);
});

test("mobile touch episode, methods and diagnostics at narrow and tablet widths", async ({
  browser,
}) => {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:4174",
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/#world");
  await page.getByRole("button", { name: "Later observer", exact: true }).tap();
  await page.locator('[data-event="h72"]').tap();
  await expect(page.locator(".episode-caption")).toContainText(
    "Score the forecast",
  );
  await page.locator(".layer-choices button").first().tap();
  await expect(page.locator(".episode-scene svg")).toContainText(
    "ILLUSTRATIVE",
  );
  await page.locator("details").evaluateAll((ds) =>
    ds.forEach((d) => {
      if (d instanceof HTMLDetailsElement) d.open = true;
    }),
  );
  for (const width of [320, 375, 390, 768, 1024]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `overflow at ${width}`,
    ).toBe(true);
    const contained = await page.evaluate(() => {
      const pairs = [
        [".experiment-layout", ".story-results"],
        [".question-layout", ".question-copy"],
      ];
      return (
        pairs.every(
          ([parent, child]) =>
            document.querySelector(parent)!.getBoundingClientRect().bottom +
              1 >=
            document.querySelector(child)!.getBoundingClientRect().bottom,
        ) &&
        document.querySelector(".story-caveat")!.getBoundingClientRect().top >=
          document.querySelector(".story-results")!.getBoundingClientRect()
            .bottom
      );
    });
    expect(contained, `No overlapping story content at ${width}`).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(errors).toEqual([]);
  await context.close();
});

test("a browser that throws during WebGL setup keeps the 2D exhibit and controls usable", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...args: unknown[]
    ) {
      if (type === "webgl2" || type === "webgl") {
        document.documentElement.dataset.webglAttempt = "blocked";
        throw Error("WebGL disabled by browser");
      }
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.goto("/");
  await page.locator(".hero-instrument").scrollIntoViewIfNeeded();
  await expect(page.locator("html")).toHaveAttribute(
    "data-webgl-attempt",
    "blocked",
  );
  await page.getByRole("button", { name: "24 h only", exact: true }).click();
  await expect(page.getByTestId("hero-response")).toHaveText(
    (0.7 * Math.exp(-1)).toFixed(4),
  );
  await expect(page.getByTestId("instrument-fallback")).toBeVisible();
  await expect(page.locator(".instrument-visual canvas")).toHaveCount(0);
  expect(errors).toEqual([]);
});
