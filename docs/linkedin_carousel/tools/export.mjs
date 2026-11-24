// Export output/carousel.html to the LinkedIn PDF, 1080x1350 page PNGs and previews.
// Fails if any page overflows, any element leaves its page, or any text is clipped.
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "playwright-core";

const HERE = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(HERE, "output");
const PDF = join(OUT, "CMJ_From_Force_Plate_to_Forecast_carousel.pdf");
const PNG_DIR = join(OUT, "pages");
const PREVIEW_DIR = join(OUT, "previews");
const PAGE_W = 1080;
const PAGE_H = 1350;
const PAGES = 10;

const browser = await chromium.launch();
try {
  const context = await browser.newContext({ viewport: { width: PAGE_W, height: PAGE_H }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("requestfailed", (r) => errors.push(`failed ${r.url()}`));
  await page.goto(pathToFileURL(join(OUT, "carousel.html")).href);
  await page.waitForFunction(() => window.__carouselReady === true, null, { timeout: 30000 });
  if (errors.length) throw new Error(`page errors:\n${errors.join("\n")}`);

  // Layout QA: content must stay above the footer and inside the page and its boxes.
  const problems = await page.evaluate(() => {
    const out = [];
    const fonts = [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family);
    for (const family of ['"Geist"', '"Geist Mono"', '"Source Serif 4"']) {
      if (!fonts.some((f) => f === family || `"${f}"` === family)) out.push(`font not loaded: ${family}`);
    }
    for (const section of document.querySelectorAll(".page")) {
      const n = section.dataset.page;
      const box = section.getBoundingClientRect();
      const footer = section.querySelector(".footer").getBoundingClientRect();
      for (const child of section.children) {
        if (child.classList.contains("footer")) continue;
        const r = child.getBoundingClientRect();
        if (r.bottom > footer.top - 12) out.push(`page ${n}: ${child.tagName}.${child.className} ends at ${Math.round(r.bottom - box.top)} px, footer starts at ${Math.round(footer.top - box.top)} px`);
        if (r.right > box.right - 40 || r.left < box.left + 40) out.push(`page ${n}: ${child.tagName}.${child.className} breaks the side gutter`);
      }
      for (const el of section.querySelectorAll("*")) {
        if (el.closest("svg") && el.tagName !== "svg") continue;
        if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflow !== "visible") out.push(`page ${n}: clipped ${el.tagName}.${el.className}`);
      }
      for (const svg of section.querySelectorAll("svg.fig")) {
        const s = svg.getBoundingClientRect();
        const boxes = [];
        for (const t of svg.querySelectorAll("text")) {
          const r = t.getBoundingClientRect();
          if (r.width === 0) continue;
          if (r.left < s.left - 1 || r.right > s.right + 1 || r.top < s.top - 1 || r.bottom > s.bottom + 1) out.push(`page ${n}: SVG text outside its figure: "${t.textContent}"`);
          boxes.push([t.textContent, r]);
        }
        // Figure labels must not overlap one another (2 px tolerance for ascender/descender boxes).
        for (let i = 0; i < boxes.length; i++) {
          for (let j = i + 1; j < boxes.length; j++) {
            const [a, ra] = boxes[i];
            const [b, rb] = boxes[j];
            const overlapX = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
            const overlapY = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
            if (overlapX > 2 && overlapY > 4) out.push(`page ${n}: overlapping labels "${a}" and "${b}"`);
          }
        }
      }
      // Phone readability: no rendered text below 26 px (9.4 px at 390 px width); subscripts
      // inside equations and figure legends may go to 22 px.
      for (const el of section.querySelectorAll("*")) {
        const hasText = [...el.childNodes].some((c) => c.nodeType === 3 && c.textContent.replace(/[\s\u200b]/g, ""));
        if (!hasText) continue;
        const size = parseFloat(getComputedStyle(el).fontSize);
        // Script-size parts of equations (fraction terms, sub/superscripts) may go to 20 px.
        const script = el.closest(".katex, sub, sup") || el.getAttribute("baseline-shift");
        if (size < (script ? 20 : 26)) out.push(`page ${n}: ${size}px text "${el.textContent.trim().slice(0, 40)}"`);
      }
    }
    return out;
  });
  if (problems.length && !process.env.CAROUSEL_QA_SOFT) throw new Error(`layout QA failed:\n${problems.join("\n")}`);
  if (problems.length) console.warn(`layout QA (soft):\n${problems.join("\n")}`);

  // Page PNGs at exactly 1080x1350.
  rmSync(PNG_DIR, { recursive: true, force: true });
  mkdirSync(PNG_DIR, { recursive: true });
  const sections = page.locator(".page");
  if ((await sections.count()) !== PAGES) throw new Error(`expected ${PAGES} pages`);
  for (let i = 0; i < PAGES; i++) {
    await sections.nth(i).screenshot({ path: join(PNG_DIR, `page-${String(i + 1).padStart(2, "0")}.png`), animations: "disabled" });
  }

  // Flattened vector PDF; links stay clickable. Title comes from <title>.
  await page.emulateMedia({ media: "print" });
  await page.pdf({ path: PDF, width: `${PAGE_W}px`, height: `${PAGE_H}px`, printBackground: true, preferCSSPageSize: true, tagged: true });

  // Previews: contact sheet and phone-width renders (390 CSS px, 3x density).
  rmSync(PREVIEW_DIR, { recursive: true, force: true });
  mkdirSync(join(PREVIEW_DIR, "phone"), { recursive: true });
  mkdirSync(join(PREVIEW_DIR, "phone-natural"), { recursive: true });
  const imgs = Array.from({ length: PAGES }, (_, i) => `../pages/page-${String(i + 1).padStart(2, "0")}.png`);
  const sheet = `<!doctype html><meta charset="utf-8"><style>
    body{margin:0;background:#ebe7da;font:500 22px Geist Mono,monospace;color:#566169}
    .grid{display:grid;grid-template-columns:repeat(5,360px);gap:24px;padding:40px}
    figure{margin:0}img{width:360px;height:450px;display:block;box-shadow:0 2px 10px #202c3322}
    figcaption{margin-top:10px}</style>
    <div class="grid">${imgs.map((s, i) => `<figure><img src="${s}"><figcaption>${String(i + 1).padStart(2, "0")} / ${String(PAGES).padStart(2, "0")}</figcaption></figure>`).join("")}</div>`;
  const sheetFile = join(PREVIEW_DIR, "_contact_sheet.html");
  writeFileSync(sheetFile, sheet);
  const sheetPage = await context.newPage();
  await sheetPage.setViewportSize({ width: 5 * 360 + 4 * 24 + 80, height: 2 * 492 + 24 + 80 });
  await sheetPage.goto(pathToFileURL(sheetFile).href);
  await sheetPage.waitForLoadState("load");
  await sheetPage.screenshot({ path: join(PREVIEW_DIR, "contact_sheet.png"), fullPage: true });
  rmSync(sheetFile);

  // Each page shown 390 CSS px wide, as in the LinkedIn feed: at 3x density (phone pixels)
  // and at 1x (natural CSS size, the strictest legibility check).
  for (const [folder, scale] of [["phone", 3], ["phone-natural", 1]]) {
    const phone = await browser.newContext({ viewport: { width: 390, height: 488 }, deviceScaleFactor: scale });
    const phonePage = await phone.newPage();
    for (let i = 0; i < PAGES; i++) {
      const file = join(PREVIEW_DIR, `_phone.html`);
      writeFileSync(file, `<!doctype html><meta charset="utf-8"><style>body{margin:0}img{width:390px;height:487.5px;display:block}</style><img src="../pages/page-${String(i + 1).padStart(2, "0")}.png">`);
      await phonePage.goto(pathToFileURL(file).href);
      await phonePage.waitForLoadState("load");
      await phonePage.screenshot({ path: join(PREVIEW_DIR, folder, `phone-${String(i + 1).padStart(2, "0")}.png`) });
      rmSync(file);
    }
    await phone.close();
  }
  console.log(`exported ${PAGES} pages, PDF, contact sheet and phone previews`);
} finally {
  await browser.close();
}
