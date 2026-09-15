import {test,expect} from '@playwright/test';

test('comparison exposes independent population origin and election selectors inside the election map',async({page})=>{
 await page.goto('./?view=compare&metric=foreign_background_pct&party=SD&municipality=0180');
 await expect(page.locator('#metric').locator('..')).toContainText('Origen poblacional');
 await expect(page.locator('#compare-election')).toBeVisible();
 await expect(page.locator('#compare-election option[value=winning_party]')).toHaveText('Partido dominante');
 await expect(page.locator('#compare-election option[value=winning_block]')).toHaveText('Bloque dominante');
 await page.selectOption('#compare-election','winning_block');
 await expect(page.locator('#map-right')).toHaveAttribute('data-metric','winning_block');
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','foreign_background_pct');
 await expect(page.locator('#party')).toHaveValue('winning_block');
 await expect(page.locator('#right-legend')).toContainText('S · V · MP · C');
 await page.reload();await expect(page.locator('#compare-election')).toHaveValue('winning_block');
 await page.selectOption('#party','winning_party');
 await expect(page.locator('#compare-election')).toHaveValue('winning_party');
 await expect(page.locator('#map-right')).toHaveAttribute('data-metric','winning_party');
 await expect(page.locator('#right-legend .party-badge')).toHaveCount(9);
 await page.selectOption('#compare-election','S');await expect(page.locator('#map-right')).toHaveAttribute('data-metric','pct_S');
 await page.selectOption('#metric','born_sweden_pct');await expect(page.locator('#map-left')).toHaveAttribute('data-metric','born_sweden_pct');
 await expect(page.locator('#map-right')).toHaveAttribute('data-metric','pct_S');
 await page.setViewportSize({width:390,height:844});await expect(page.locator('#compare-election')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
