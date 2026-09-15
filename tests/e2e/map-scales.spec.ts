import {test,expect} from '@playwright/test';
test('map gradients and legend share national limits, stable across territory filters',async({page})=>{
 await page.goto('./?view=compare&party=V&metric=born_rest_world_unknown_pct&municipality=0180');
 await expect(page.locator('#map-right')).toHaveAttribute('data-ready','true');
 const max=await page.locator('#map-right').getAttribute('data-scale-max');
 expect(Number(max)).toBeLessThan(50);
 await expect(page.locator('#right-legend .scale')).toHaveAttribute('data-scale-max',max!);
 const leftMax=await page.locator('#map-left').getAttribute('data-scale-max');
 await expect(page.locator('#legend .scale')).toHaveAttribute('data-scale-max',leftMax!);
 await page.selectOption('#municipality','');
 await expect(page.locator('#map-right')).toHaveAttribute('data-scale-max',max!);
 await expect(page.locator('#map-left')).toHaveAttribute('data-scale-max',leftMax!);
 await page.selectOption('#compare-election','M');
 await expect(page.locator('#right-legend .scale')).toHaveAttribute('data-scale-max',(await page.locator('#map-right').getAttribute('data-scale-max'))!);
 await expect(page.locator('#map-left')).toHaveAttribute('data-scale-max',leftMax!);
 await page.selectOption('#compare-election','winning_party');
 await expect(page.locator('#right-legend .party-badge')).toHaveCount(9);
 await expect(page.locator('#right-legend .scale')).toHaveCount(0);
});
