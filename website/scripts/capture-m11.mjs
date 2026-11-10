// Capture matched before/after screenshots of a static export for M11 qualification.
// Usage: node scripts/capture-m11.mjs <export-dir> <label> [routes...]
// Serves the export on an isolated port, hides fixed chrome only for element shots, and
// writes PNGs plus a JSON log of overflow and console errors to docs/m11/<label>/.
import { chromium } from "@playwright/test";
import { createServer } from "node:http";
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { extname, join, resolve } from "node:path";

const [dir, label, ...rest] = process.argv.slice(2);
if (!dir || !label) throw new Error("usage: capture-m11.mjs <export-dir> <label> [routes...]");
const root = resolve(dir);
const routes = rest.length ? rest : ["/"];
const out = resolve("docs/m11", label);
mkdirSync(out, { recursive: true });
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".pdf": "application/pdf", ".txt": "text/plain" };
const server = createServer((req, res) => {
  let path = join(root, decodeURIComponent(new URL(req.url, "http://x").pathname));
  try {
    if (statSync(path).isDirectory()) path = join(path, "index.html");
    res.writeHead(200, { "content-type": types[extname(path)] ?? "application/octet-stream" });
    res.end(readFileSync(path));
  } catch {
    res.writeHead(404).end("not found");
  }
}).listen(0, "127.0.0.1");
await new Promise((r) => server.once("listening", r));
const base = `http://127.0.0.1:${server.address().port}`;

const VIEWPORTS = [
  { id: "desktop", width: 1440, height: 1000 },
  { id: "tablet-portrait", width: 834, height: 1112, touch: true },
  { id: "tablet-landscape", width: 1112, height: 834, touch: true },
  { id: "mobile-portrait", width: 390, height: 844, touch: true },
  { id: "mobile-landscape", width: 844, height: 390, touch: true },
];
const browser = await chromium.launch({ args: ["--enable-unsafe-swiftshader"] });
const log = [];
for (const vp of VIEWPORTS) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    hasTouch: Boolean(vp.touch),
    isMobile: Boolean(vp.touch) && vp.width < 900,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  for (const route of routes) {
    const res = await page.goto(base + route, { waitUntil: "networkidle" });
    await page.waitForTimeout(700);
    const name = route === "/" ? "overview" : route.replace(/^\/|\/$/g, "").replace(/[^a-z0-9]+/gi, "-");
    await page.screenshot({ path: join(out, `${name}-${vp.id}.png`) });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    log.push({ viewport: vp.id, route, status: res?.status() ?? null, horizontalOverflowPx: overflow });
  }
  if (errors.length) log.push({ viewport: vp.id, consoleErrors: errors });
  await context.close();
}
await browser.close();
server.close();
writeFileSync(join(out, "capture-log.json"), `${JSON.stringify({ label, routes, viewports: VIEWPORTS, results: log }, null, 2)}\n`);
console.log(`${label}: ${log.length} records → ${out}`);
