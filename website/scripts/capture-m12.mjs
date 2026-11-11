// Capture matched before/after screenshots. usage: node scripts/capture-m12.mjs <outDir> <label> <dist>
import { chromium } from "@playwright/test";
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
const [outDir, label, dist] = process.argv.slice(2);
mkdirSync(outDir, { recursive: true });
const srv = spawn("python3", ["-m", "http.server", "4176", "--bind", "127.0.0.1", "--directory", dist]);
await new Promise((r) => setTimeout(r, 1000));
const b = await chromium.launch({ args: ["--enable-unsafe-swiftshader"] });
for (const [name, vp, mobile] of [["desktop", { width: 1440, height: 1000 }, false], ["mobile", { width: 390, height: 844 }, true]]) {
  const c = await b.newContext({ viewport: vp, isMobile: mobile, hasTouch: mobile, reducedMotion: "reduce" });
  const p = await c.newPage();
  for (const [route, slug] of [["/", "home"], ["/paper/", "paper"], ["/results/", "results"], ["/models/", "models"]]) {
    await p.goto(`http://127.0.0.1:4176${route}`);
    await p.waitForTimeout(600);
    await p.screenshot({ path: `${outDir}/${label}-${slug}-${name}.png` });
  }
  await c.close();
}
await b.close();
srv.kill();
