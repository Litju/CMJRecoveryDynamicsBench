import { chromium } from "@playwright/test";
import { mkdir, writeFile, readFile, readdir } from "node:fs/promises";
import { gzipSync } from "node:zlib";
const baseURL = process.env.CMJ_PREVIEW_URL || "http://127.0.0.1:4173";
await mkdir("docs/screenshots", { recursive: true });
const browser = await chromium.launch({
  args: ["--enable-unsafe-swiftshader"],
});
const errors = [];
const captures = [];
for (const [device, viewport] of [
  ["desktop", { width: 1440, height: 1000 }],
  ["mobile", { width: 390, height: 844 }],
]) {
  const page = await browser.newPage({
    viewport,
    reducedMotion: device === "mobile" ? "reduce" : "no-preference",
    isMobile: device === "mobile",
    hasTouch: device === "mobile",
  });
  page.on("pageerror", (error) => errors.push(`${device}: ${error.message}`));
  await page.goto(baseURL, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({
    content:
      ".story-progress{position:relative!important;top:auto!important;} .skip-link{display:none!important;}",
  });
  for (const id of [
    "hero",
    "quick-route",
    "question",
    "world",
    "lineage",
    "experiment",
    "explorer",
    "remaining",
    "lab",
    "evidence",
  ]) {
    const locator = page.locator(
      id === "hero"
        ? ".hero"
        : id === "quick-route"
          ? ".quick-route"
          : `#${id}`,
    );
    await locator.scrollIntoViewIfNeeded();
    if (device === "desktop" && id === "remaining")
      await page.locator(".instrument-visual canvas").waitFor();
    if (id === "experiment")
      await page
        .locator("#experiment")
        .evaluate((e) => e.setAttribute("data-entered", "true"));
    const path = `docs/screenshots/${device}-${id}.png`;
    await locator.screenshot({ path, animations: "disabled" });
    captures.push({ device, chapter: id, path });
  }
  for (const [chapter, selector] of [
    ["apparatus", ".measurement-exhibit"],
    ["exposure", ".exposure-context"],
    ["history", ".history-reader"],
  ]) {
    await page
      .locator(selector)
      .screenshot({
        path: `docs/screenshots/${device}-${chapter}.png`,
        animations: "disabled",
      });
    captures.push({
      device,
      chapter,
      path: `docs/screenshots/${device}-${chapter}.png`,
    });
  }
  for (const [index, chapter] of [
    [1, "impulse"],
    [2, "innovation"],
  ]) {
    await page.locator(".measurement-tabs button").nth(index).click();
    await page
      .locator(".measurement-workbench")
      .screenshot({
        path: `docs/screenshots/${device}-${chapter}.png`,
        animations: "disabled",
      });
    captures.push({
      device,
      chapter,
      path: `docs/screenshots/${device}-${chapter}.png`,
    });
  }
  await page.locator('[data-event="h72"]').click();
  await page
    .getByRole("button", { name: "Later observer", exact: true })
    .click();
  await page.locator(".layer-choices button").first().click();
  await page.locator("#world .methods-sheet summary").click();
  await page.locator("#world").screenshot({
    path: `docs/screenshots/${device}-world-revealed.png`,
    animations: "disabled",
  });
  await page
    .getByRole("button", { name: "Opposing modes", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Accumulated area", exact: true })
    .click();
  await page.locator("#lab .methods-sheet summary").click();
  await page.locator("#lab").screenshot({
    path: `docs/screenshots/${device}-lab-methods.png`,
    animations: "disabled",
  });
  captures.push(
    {
      device,
      chapter: "world-revealed",
      path: `docs/screenshots/${device}-world-revealed.png`,
    },
    {
      device,
      chapter: "lab-methods",
      path: `docs/screenshots/${device}-lab-methods.png`,
    },
  );
  await page
    .locator(".layer-choices")
    .getByRole("button", { name: /Observation/ })
    .click();
  await page
    .getByRole("button", { name: "Net-impulse area", exact: true })
    .click();
  await page.locator(".layer-exhibit").screenshot({
    path: `docs/screenshots/${device}-measurement.png`,
    animations: "disabled",
  });
  await page.locator(".study-methods > .methods-sheet > summary").click();
  await page.locator(".study-methods > .methods-sheet").screenshot({
    path: `docs/screenshots/${device}-selection.png`,
    animations: "disabled",
  });
  captures.push(
    {
      device,
      chapter: "measurement",
      path: `docs/screenshots/${device}-measurement.png`,
    },
    {
      device,
      chapter: "selection",
      path: `docs/screenshots/${device}-selection.png`,
    },
  );
  const panel = page.locator(
    device === "mobile" ? ".mobile-lineage-detail" : ".desktop-lineage-detail",
  );
  await panel.locator(".formulation-methods summary").click();
  await panel.locator(".lineage-evidence summary").click();
  await panel.screenshot({
    path: `docs/screenshots/${device}-formulation-methods.png`,
    animations: "disabled",
  });
  captures.push({
    device,
    chapter: "formulation-methods",
    path: `docs/screenshots/${device}-formulation-methods.png`,
  });
  await page.close();
}
const performance = [];
for (const reducedMotion of ["reduce", "no-preference"]) {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    reducedMotion,
  });
  await page.addInitScript(() => {
    window.cmjLongTasks = [];
    new PerformanceObserver((list) =>
      window.cmjLongTasks.push(
        ...list
          .getEntries()
          .map((e) => ({ start: e.startTime, duration: e.duration })),
      ),
    ).observe({ type: "longtask", buffered: true });
  });
  await page.goto(baseURL, { waitUntil: "networkidle" });
  if (reducedMotion === "no-preference") {
    await page.locator(".hero-instrument").scrollIntoViewIfNeeded();
    await page.locator(".instrument-visual canvas").waitFor();
  }
  const timings = await page.locator(".model-options").evaluate(async (box) => {
    const times = [];
    for (let i = 0; i < 20; i++) {
      const start = performance.now();
      box.querySelectorAll("button")[i % 4].click();
      await new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      );
      times.push(performance.now() - start);
    }
    return times.sort((a, b) => a - b);
  });
  const metrics = await page.evaluate(() => ({
    navigation: performance.getEntriesByType("navigation")[0].toJSON(),
    longTasks: window.cmjLongTasks,
    userAgent: navigator.userAgent,
    resources: performance
      .getEntriesByType("resource")
      .filter((e) => e.initiatorType === "script")
      .map((e) => ({
        name: new URL(e.name).pathname,
        bytes: e.decodedBodySize,
      })),
    canvases: document.querySelectorAll("canvas").length,
  }));
  performance.push({
    reducedMotion,
    modelSwitchTwoFramesMs: {
      median: timings[10],
      p95: timings[18],
      max: timings[19],
    },
    ...metrics,
  });
  await page.close();
}
const chunks = [];
for (const file of await readdir("out/_next/static/chunks")) {
  if (!file.endsWith(".js")) continue;
  const content = await readFile(`out/_next/static/chunks/${file}`);
  chunks.push({
    file,
    bytes: content.length,
    gzipBytes: gzipSync(content).length,
  });
}
await writeFile(
  "docs/browser-evidence.json",
  JSON.stringify(
    {
      baseURL,
      capturedAt: new Date().toISOString(),
      captures,
      errors,
      performance,
      chunks,
    },
    null,
    2,
  ) + "\n",
);
await browser.close();
if (errors.length) throw Error(errors.join("\n"));
console.log(
  `Captured ${captures.length} chapter/state screenshots; browser errors: ${errors.length}. Performance saved to docs/browser-evidence.json.`,
);
