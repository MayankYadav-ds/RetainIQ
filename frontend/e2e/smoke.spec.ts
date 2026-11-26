import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
test('built frontend connects to actual backend and survives API failure', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Backend connected')).toBeVisible();
  await expect(page.getByText('v0.1.0 · Database reachable')).toBeVisible();
  const ready = await page.request.get('http://127.0.0.1:8000/ready');
  expect(await ready.json()).toEqual({status:'ready', database:'reachable'});
  await page.route('**/ready', route => route.fulfill({status:503, body:'{}', headers:{'Access-Control-Allow-Origin':'http://127.0.0.1:4173'}}));
  await page.reload();
  await expect(page.getByText('Backend unavailable')).toBeVisible();
  await page.unroute('**/ready');
  await page.getByRole('button', {name:'Retry'}).click();
  await expect(page.getByText('Backend connected')).toBeVisible();
});
test('responsive shell has no overflow or automated accessibility violations', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Backend connected')).toBeVisible();
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  await page.getByRole('button',{name:'Dark theme'}).click();
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  await page.setViewportSize({width:375,height:812});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await expect(page.getByRole('heading',{level:1})).toBeVisible();
});
