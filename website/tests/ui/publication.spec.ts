import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import fixture from "../../src/data/manuscript.json";
const ROUTES = ["/results/", "/models/", "/methods/", "/evidence/", "/paper/"];
const FIGURE_ROUTE: Record<number, string> = Object.fromEntries(
  fixture.figures.map((f) => [f.number, f.route]),
);

function trackErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

test("research areas are navigable and the paper is served as verified PDFs", async ({ page, request }) => {
  const errors = trackErrors(page);
  await page.goto("/");
  const nav = page.getByRole("navigation", { name: "Main navigation" });
  await expect(nav.getByRole("link")).toHaveText([
    "The science",
    "Results",
    "Architectures",
    "Methods",
    "Verification",
    "Research paper",
  ]);
  await expect(nav.getByRole("link", { name: "The science" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.getByRole("link", { name: "Read the flagship paper" })).toHaveAttribute("href", "/paper/");
  await expect(page.getByRole("link", { name: "full illustrated paper" })).toHaveAttribute(
    "href",
    "/paper/flagship/full_illustrated_manuscript.pdf",
  );
  for (const route of ROUTES) {
    await nav.getByRole("link").nth(ROUTES.indexOf(route) + 1).click();
    await expect(page).toHaveURL(new RegExp(`${route}$`));
    await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
    await expect(nav.locator('[aria-current="page"]')).toHaveCount(1);
  }
  for (const file of fixture.paper.files) {
    const res = await request.get(file.href);
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toContain("pdf");
    const body = await res.body();
    expect(body.length).toBe(file.bytes);
    expect(body.subarray(0, 5).toString()).toBe("%PDF-");
  }
  expect(errors).toEqual([]);
});

test("all ten figures carry a question, manuscript page, data table, limitations and exports", async ({ page }) => {
  for (const n of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
    await page.goto(`${FIGURE_ROUTE[n]}#fig-${n}`);
    const fig = page.locator(`figure#fig-${n}`);
    const meta = fixture.figures[n - 1];
    await expect(fig.locator(".pub-question")).toContainText(meta.question);
    await expect(fig.locator(".pub-page-link")).toHaveAttribute("href", `/paper/full_illustrated_research_manuscript.pdf#page=${meta.page}`);
    await expect(fig.locator(".pub-limits li").first()).toBeVisible();
    await expect(fig.locator("table.pub-table tbody tr").first()).toBeAttached();
    await expect(fig.getByRole("button", { name: "CSV" })).toBeVisible();
    await expect(fig.getByRole("button", { name: "JSON" })).toBeVisible();
    await expect(fig.getByRole("button", { name: "SVG" })).toBeVisible();
  }
});

test("exports download source-backed CSV, JSON and self-contained SVG", async ({ page }) => {
  await page.goto("/results/#fig-6");
  const fig = page.locator("figure#fig-6");
  const csv = await Promise.all([page.waitForEvent("download"), fig.getByRole("button", { name: "CSV" }).click()]);
  const csvText = readFileSync(await csv[0].path(), "utf8");
  expect(csv[0].suggestedFilename()).toBe("observatory-fig6.csv");
  expect(csvText.split("\n")[0]).toBe("Cell,Model,Target unit,Root A,Root B,Root C,Mean,Sample SD");
  expect(csvText).toContain("H24 Mean concentric force,Ridge regression,N/kg,0.630319,0.630139,0.612765,0.624408");
  const json = await Promise.all([page.waitForEvent("download"), fig.getByRole("button", { name: "JSON" }).click()]);
  const parsed = JSON.parse(readFileSync(await json[0].path(), "utf8"));
  expect(parsed.data.aggregates.ridge_full.mean).toBe(fixture.data.sixCell.aggregates.ridge_full.mean);
  expect(parsed.provenance).toContain(fixture.paper.artifactManifestSha256);
  const svg = await Promise.all([page.waitForEvent("download"), fig.getByRole("button", { name: "SVG" }).click()]);
  const svgText = readFileSync(await svg[0].path(), "utf8");
  expect(svgText.startsWith("<?xml")).toBe(true);
  expect((svgText.match(/<svg/g) ?? []).length).toBe(7); // composite + six panels
  expect(svgText).toContain("H72, Net-impulse innovation"); // panel accessible name
  expect(svgText).toContain("cell-mean predictor = 1");
  expect(svgText).not.toContain("data-export-ignore");
});

test("deep links restore figure state and controls update the URL", async ({ page }) => {
  await page.goto("/results/?f7root=B#fig-7");
  const fig7 = page.locator("figure#fig-7");
  await expect(fig7.getByRole("button", { name: "Root B" })).toHaveAttribute("aria-pressed", "true");
  const ridgeB = fixture.data.sixCell.aggregates.ridge_full.roots[1];
  await expect(fig7.locator(".pub-readout")).toContainText(ridgeB.toFixed(6));
  await fig7.getByRole("button", { name: "Across-root mean" }).click();
  await expect(page).not.toHaveURL(/f7root/);
  await fig7.getByRole("button", { name: "Root C" }).click();
  await expect(page).toHaveURL(/f7root=C/);
  await page.goto("/models/?f3a=M2&f3b=M7#fig-3");
  await expect(page.locator("figure#fig-3 .pub-readout")).toContainText("M2 Deep feedforward 6,850 parameters");
  await page.goto("/methods/?f1node=rich_history_camp_recovery#fig-1");
  await expect(page.locator("figure#fig-1 .pub-readout")).toContainText("Rich-history camp · Retired · direct parent not recorded");
});

test("figures are keyboard-inspectable and show exact recorded values", async ({ page }) => {
  await page.goto("/results/#fig-7");
  const cell = page.getByRole("button", { name: /: H72 Net impulse, Structured comparator, NRMSE/ });
  await cell.focus();
  await page.keyboard.press("Enter");
  const v = fixture.data.sixCell.cells.find((c) => c.cell === "H72/net_impulse_innovation")!.models;
  await expect(page.locator("figure#fig-7 .pub-readout")).toContainText(v.structured_full.mean.toFixed(6));
  await expect(page.locator("figure#fig-7 .pub-readout")).toContainText(
    `+${(v.structured_full.mean - v.ridge_full.mean).toFixed(4)} vs ridge`,
  );
  await page.goto("/results/#fig-6");
  await page.locator("#f6-cell-select").selectOption("H48-impulse");
  await expect(page.locator("figure#fig-6 .pub-readout")).toContainText("H48 · Net-impulse innovation (m/s)");
  await page.goto("/models/#fig-4");
  const route = page.getByRole("button", { name: /^M5 · r0 FAIL: route M5-r0/ });
  await route.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("figure#fig-4 .pub-readout")).toContainText("443 of 1,024 elements failing");
  await page.goto("/methods/#fig-5");
  await page.locator("#f5-time").fill("0.55");
  await expect(page.locator("figure#fig-5 .pub-readout")).toContainText("net impulse so far 2.74");
  await expect(page.locator("figure#fig-5")).toContainText("14.79 N/kg");
  await expect(page.locator("figure#fig-5")).toContainText("24.09 N/kg");
});

test("recorded aggregates and the draft status appear unchanged across the site", async ({ page }) => {
  await page.goto("/");
  for (const v of ["2.430659", "1.036038", "0.736270", "0.773316"])
    await expect(page.locator("#overview")).toContainText(v);
  await expect(page.locator("#overview")).toContainText("not athlete accuracy");
  await page.goto("/paper/");
  await expect(page.getByRole("note").first()).toContainText("Owner-review draft");
  await expect(page.locator("main")).not.toContainText(/peer-reviewed paper|published in|DOI: ?10\./i);
  await page.goto("/evidence/");
  await expect(page.locator("#citations")).toContainText("version 1.1.0");
  await expect(page.locator("#citations a").first()).toHaveAttribute("href", /\/blob\/v1\.1\.0\/CITATION\.cff$/);
});

test("phones keep navigation, avoid page overflow and scroll dense figures in place", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const page = await context.newPage();
  for (const route of ["/", ...ROUTES]) {
    await page.goto(route);
    await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, route).toBeLessThanOrEqual(0);
  }
  await page.goto("/models/#fig-3");
  const chart = page.locator("figure#fig-3 .pub-chart");
  const scrollable = await chart.evaluate((el) => el.scrollWidth > el.clientWidth);
  expect(scrollable).toBe(true);
  await context.close();
});
