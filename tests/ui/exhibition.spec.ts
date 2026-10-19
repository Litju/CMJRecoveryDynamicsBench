import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import exhibit from '../../src/data/exhibition.json';
async function range(page: Page, selector: string, value: string) {
  await page.locator(selector).evaluate((input, value) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, value);
    input.dispatchEvent(new Event('input', {bubbles:true}));
    input.dispatchEvent(new Event('change', {bubbles:true}));
  }, value);
}
test('episode boundary, all events and layers, keyboard, playback and reset', async ({page}) => {
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/#world');
  const scene = page.locator('.episode-scene');
  for (const event of exhibit.events) {
    await page.locator(`[data-event="${event.id}"]`).click();
    await expect(page.locator('.episode-caption h3')).toHaveText(event.title);
    await expect(scene).toHaveAttribute('data-perspective','model');
    await expect(page.locator('.episode-boundary')).toContainText('future outcomes are withheld');
    await expect(page.locator(`[data-event="${event.id}"]`)).toHaveAttribute('data-predictor',String(event.available));
  }
  await page.getByRole('button',{name:'Later observer',exact:true}).click();
  await expect(scene).toHaveAttribute('data-perspective','observer');
  await expect(scene.locator('svg')).toContainText('✓');
  await expect(page.locator('.episode-boundary')).toContainText('remain excluded');
  for (const layer of exhibit.layers) {
    await page.locator('.layer-choices').getByRole('button',{name:new RegExp(layer.label)}).click();
    await expect(page.locator('.layer-detail h3')).toHaveText(layer.title);
    await expect(scene).toHaveAttribute('data-layer',layer.id);
  }
  await page.locator('#episode-time').focus();
  await page.keyboard.press('Home');
  await expect(page.locator('#episode-time')).toHaveValue('0');
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('#episode-time')).toHaveValue('1');
  await page.getByRole('button',{name:'Play episode',exact:true}).click();
  await expect(page.locator('#episode-time')).not.toHaveValue('1');
  await page.getByRole('button',{name:'Pause episode',exact:true}).click();
  await page.getByRole('button',{name:'Reset episode',exact:true}).click();
  await expect(page.locator('#episode-time')).toHaveValue('2');
  await expect(scene).toHaveAttribute('data-layer','predictor');
  await expect(scene).toHaveAttribute('data-perspective','model');
  await page.getByText('Methods & evidence · the complete predictor budget',{exact:true}).click();
  await expect(page.locator('.feature-budget article')).toHaveCount(5);
  expect((await new AxeBuilder({page}).include('#world').withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
});
