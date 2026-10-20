import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';
const phase = process.argv[2] || 'after';
assert(['before', 'after'].includes(phase));
const directory = `docs/polish/${phase}`;
const baseURL = process.env.CMJ_PREVIEW_URL || 'http://127.0.0.1:4173';
await mkdir(directory, { recursive: true });
const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader'] });
const errors = [];
try {
  for (const [device, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
    const page = await browser.newPage({ viewport: { width, height }, isMobile: device === 'mobile', hasTouch: device === 'mobile' });
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(baseURL, { waitUntil: 'networkidle' });
    await page.locator('.journey-viewport canvas').waitFor();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${directory}/${device}-journey.png` });
    // Match the baseline chapter captures without the pinned navigation obscuring figures.
    await page.addStyleTag({ content: '.journey-stage{visibility:hidden!important} .site-header,.story-progress{position:relative!important} .skip-link{display:none!important}' });
    for (const [name, selector] of [['explorer', '#explorer'], ['response', '.hero-instrument'], ['lab', '.lab-panel']]) {
      const panelHeight = await page.locator(selector).evaluate((el) => el.getBoundingClientRect().height);
      if (name === 'response') await page.setViewportSize({ width, height: Math.max(height, Math.ceil(panelHeight) + 100) });
      await page.locator(selector).scrollIntoViewIfNeeded();
      if (name === 'response') await page.locator('.instrument-visual canvas').waitFor();
      await page.waitForTimeout(600);
      await page.locator(selector).screenshot({ path: `${directory}/${device}-${name}.png` });
      await page.setViewportSize({ width, height });
    }
    await page.getByRole('button', { name: '3D comparison', exact: true }).click();
    await page.locator('.benchmark-canvas canvas').waitFor();
    await page.locator('.benchmark-3d').screenshot({ path: `${directory}/${device}-benchmark.png` });
    await page.close();
  }
  assert.deepEqual(errors, []);
  console.log(`10 ${phase} screenshots captured without page errors.`);
} finally {
  await browser.close();
}
