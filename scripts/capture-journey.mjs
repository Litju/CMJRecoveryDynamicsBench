import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const browser = await chromium.launch({ args: ["--enable-unsafe-swiftshader"] });
const captures = [];
const errors = [];
await mkdir("docs/journey", { recursive: true });
for (const [device, viewport] of [["desktop", { width: 1440, height: 1000 }], ["mobile", { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport, isMobile: device === "mobile", hasTouch: device === "mobile" });
  page.on("pageerror", (error) => errors.push(`${device}: ${error.message}`));
  await page.goto("http://127.0.0.1:4173", { waitUntil: "networkidle" });
  await page.locator(".journey-viewport canvas").waitFor();
  for (const chapter of ["intro", "question", "world", "lineage", "experiment", "explorer", "remaining", "lab", "evidence"]) {
    await page.locator(`#${chapter}`).evaluate((e) => e.scrollIntoView({ block: "start", behavior: "instant" }));
    await page.waitForFunction((id) => document.querySelector(".journey-stage")?.getAttribute("data-chapter") === id, chapter);
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const path = `docs/journey/${device}-${chapter}.png`;
    await page.screenshot({ path, animations: "disabled" });
    captures.push({ device, chapter, path });
  }
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.locator(".journey-fallback").waitFor();
  const path = `docs/journey/${device}-reduced-motion.png`;
  await page.screenshot({ path });
  captures.push({ device, chapter: "reduced-motion", path });
  await page.close();
}
await browser.close();
await writeFile("docs/journey/captures.json", JSON.stringify({ captures, errors }, null, 2) + "\n");
if (errors.length) throw Error(errors.join("\n"));
console.log(`${captures.length} chapter viewport captures; no runtime errors.`);
