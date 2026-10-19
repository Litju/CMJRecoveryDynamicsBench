import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import nodes from "../../src/data/lineage.json";
import fixture from "../../src/data/results.json";

test("story precedes the benchmark; scroll navigation and sourced result reveal work", async ({
  page,
}) => {
  await page.goto("/");
  const ids = await page
    .locator("main > section[id]")
    .evaluateAll((sections) => sections.map((s) => s.id));
  expect(ids).toEqual([
    "question",
    "lineage",
    "experiment",
    "explorer",
    "remaining",
    "lab",
    "evidence",
  ]);
  await page.getByRole("link", { name: "Start the story" }).click();
  await expect(page.locator("#question")).toContainText(
    "change from the pre-index baseline",
  );
  await expect(
    page.locator('.story-progress a[aria-current="step"]'),
  ).toHaveAttribute("href", "#question");
  await page.locator("#experiment").scrollIntoViewIfNeeded();
  await expect(page.locator("#experiment")).toHaveAttribute(
    "data-entered",
    "true",
  );
  await expect(
    page.locator('.story-progress a[aria-current="step"]'),
  ).toHaveAttribute("href", "#experiment");
  for (const [id, m] of Object.entries(fixture.models)) {
    await expect(page.locator(`[data-model="${id}"] strong`)).toHaveText(
      m.acrossRoots.root_mean_nrmse.toFixed(6),
    );
  }
  await expect(page.locator(".experiment-answer strong")).toHaveText("28.9%");
  await expect(page.locator(".story-caveat")).toContainText(
    "no ridge-versus-structured interval",
  );
  await page.locator(".model-primer summary").first().click();
  await expect(page.locator(".model-primer details").first()).toHaveAttribute(
    "open",
    "",
  );
});

test("all lineage contracts, exact statuses, parent selection and evidence are accessible by keyboard", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const panel = page.locator(".desktop-lineage-detail");
  await expect(page.locator(".lineage-node")).toHaveCount(8);
  await page.locator(".lineage-node").first().focus();
  await page.keyboard.press("Tab");
  await expect(
    page.locator(
      '[data-formulation="canonical_preseason_camp_recovery"] > button',
    ),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  for (const node of nodes) {
    const branch = page.locator(`[data-formulation="${node.id}"]`).first();
    await expect(branch).toHaveAttribute(
      "data-parent",
      node.parent ?? "unresolved",
    );
    const button = branch.locator(":scope > button");
    await button.focus();
    await page.keyboard.press("Enter");
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(panel.locator(".contract-name")).toHaveText(node.id);
    await expect(panel.locator(".lineage-question")).toHaveText(node.question);
    await expect(panel.locator(".lineage-facts")).toContainText(node.status);
    await expect(panel.locator(".lineage-evidence dd").last()).toHaveText(
      [
        "preliminary_post_exposure_recovery",
        "threshold_response_recovery",
      ].includes(node.id)
        ? "NOT_REPRODUCIBLE"
        : "HISTORICAL_EVIDENCE_ONLY",
    );
    await expect(panel.locator(".contract-link")).toHaveAttribute(
      "href",
      `https://github.com/Litju/CMJRecoveryDynamicsBench/blob/${fixture.provenance.commit}/${node.source}`,
    );
  }
  await panel.locator(".lineage-evidence summary").click();
  await expect(panel.locator(".lineage-evidence")).toContainText(
    "PARTIALLY_REPRODUCIBLE",
  );
  await expect(panel.locator(".lineage-evidence")).toContainText(
    "HISTORICAL_EVIDENCE_ONLY",
  );
  await panel.getByRole("button", { name: "Correlated exposure" }).click();
  await expect(panel.locator(".contract-name")).toHaveText(
    "correlated_exposure_recovery",
  );
  await page
    .locator('[data-formulation="threshold_response_recovery"] > button')
    .click();
  await expect(panel).toContainText("not an accepted successor");
  await panel.locator(".lineage-evidence summary").click();
  await expect(panel.locator(".lineage-evidence dd").last()).toHaveText(
    "NOT_REPRODUCIBLE",
  );
  await page
    .locator('[data-formulation="fixed_mode_discrepancy_recovery"] > button')
    .click();
  await page
    .locator(".lineage-layout")
    .screenshot({ path: "docs/lineage-desktop.png" });
  await panel.getByRole("link", { name: "Explore the active study" }).click();
  await expect(
    page.locator('.story-progress a[aria-current="step"]'),
  ).toHaveAttribute("href", "#experiment");
  await expect(page).toHaveURL(/#explorer$/);
  await expect(page.getByTestId("aggregate-score")).toHaveText("0.7363");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("mobile tap details stay next to their node; reduced motion and evidence boundaries hold", async ({
  browser,
}) => {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:4173",
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  await page.goto("/");
  for (const id of [
    "rich_history_camp_recovery",
    "threshold_response_recovery",
    "fixed_mode_discrepancy_recovery",
  ]) {
    const button = page.locator(`[data-formulation="${id}"] > button`);
    await button.tap();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(
      page.locator(".mobile-lineage-detail .contract-name"),
    ).toHaveText(id);
  }
  await page
    .locator(".mobile-lineage-detail")
    .getByRole("link", { name: "Explore the active study" })
    .tap();
  await expect(page).toHaveURL(/#explorer$/);
  await page.locator("#experiment").scrollIntoViewIfNeeded();
  await expect(page.locator(".bar-track > span").first()).toHaveCSS(
    "animation-name",
    "none",
  );
  await expect(page.locator(".evidence-ladder")).toContainText(
    "WHAT IS NOT ESTABLISHED",
  );
  await expect(page.locator(".new-studies")).toContainText(
    "never ranked with active NRMSE",
  );
  await page
    .locator('[data-formulation="fixed_mode_discrepancy_recovery"] > button')
    .tap();
  await page.locator(".mobile-lineage-detail .lineage-evidence summary").tap();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page
    .locator(".mobile-lineage-detail")
    .screenshot({ path: "docs/lineage-mobile.png" });
  for (const width of [320, 375, 390, 768]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `No overflow at ${width}`,
    ).toBe(true);
  }
  await context.close();
});
