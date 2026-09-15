import {test,expect,type Page} from '@playwright/test';
async function showHover(page:Page,selector:string){
 const box=await page.locator(selector).boundingBox();
 if(!box)throw new Error('No map bounds');
 for(const y of [.45,.55,.35,.65,.25])for(const x of [.5,.6,.4,.7,.3]){
  await page.mouse.move(box.x+box.width*x,box.y+box.height*y);await page.waitForTimeout(90);
  if(await page.locator('.atlas-hover .hover-card').isVisible()){await page.waitForTimeout(180);if(await page.locator('.atlas-hover .hover-card').isVisible())return;}
 }
 throw new Error('Could not hover a visible polygon');
}
test('colorful district hovers and categorical party, block and origin maps',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
 await page.goto('./?year=2026&view=electoral&metric=winning_party&municipality=0180');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});
 await expect(page.locator('.party-legend .party-badge')).toHaveCount(9);await expect(page.locator('#party')).toBeVisible();await expect(page.locator('#party')).toHaveValue('winning_party');
 await showHover(page,'#map-left');await expect(page.locator('.atlas-hover .hover-runners .party-badge')).toHaveCount(3);
 await expect(page.locator('.atlas-hover')).toContainText('Participación');
 const hoverBox=await page.locator('.atlas-hover').boundingBox();expect(hoverBox!.width).toBeLessThanOrEqual(240);expect(hoverBox!.height).toBeLessThan(270);
 await expect(page.locator('.release-notice')).not.toHaveAttribute('open','');
 await page.locator('.release-notice summary').click();await expect(page.locator('.release-notice p')).toBeVisible();await page.locator('.release-notice summary').click();
 await showHover(page,'#map-left');
 await page.screenshot({path:'tests/artifacts/hover-party.png'});
 await page.mouse.move(0,0);await page.selectOption('#metric','winning_block');
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','winning_block');
 await expect(page.locator('#legend')).toContainText('S · V · MP · C');await expect(page.locator('.district-birth-notice')).toContainText('No representa');
 await page.locator('.district-birth-notice summary').click();await expect(page.locator('.district-birth-notice p')).toBeVisible();
 await page.reload();await expect(page.locator('#metric')).toHaveValue('winning_block');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});await showHover(page,'#map-left');
 await page.screenshot({path:'tests/artifacts/hover-block.png'});
 await page.click('[data-view=demography]');await page.selectOption('#metric','common_origin');
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','common_origin');await expect(page.locator('#legend')).toContainText('excluye Suecia');
 await page.click('[data-view=compare]');await expect(page.locator('#map-right')).toHaveAttribute('data-metric','pct_SD');
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','common_origin');
 const download=page.waitForEvent('download');await page.click('#download');const stream=await (await download).createReadStream();let csv='';for await(const c of stream!)csv+=c.toString();expect(csv).toContain('winning_block');expect(csv).toContain('common_origin_definition');
 await page.click('[data-view=electoral]');await page.selectOption('#metric','party');
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','party');await expect(page.locator('#party')).toBeVisible();await page.selectOption('#party','S');await expect(page.locator('#map-count')).toContainText('Voto S');
 await page.locator('.map-options>summary').click();await page.selectOption('#quality','high');await expect(page.locator('#quality')).toHaveValue('high');
 expect(errors).toEqual([]);
});
test('municipal common country and continental subtotal categories',async({page})=>{
 await page.goto('countries/?mode=common&municipality=1280&country=SY');
 await expect(page.locator('#country-map')).toHaveAttribute('data-ready','true',{timeout:30000});
 await expect(page.locator('#birth-mode')).toHaveValue('common');await expect(page.locator('#birth-country')).toBeDisabled();
 await expect(page.locator('#country-legend')).toContainText('País extranjero más común');await expect(page.locator('.common-origin-panel')).toContainText('Malmö');
 await showHover(page,'#country-map');await expect(page.locator('.atlas-hover .origin-ranking>div')).toHaveCount(3);
 await page.screenshot({path:'tests/artifacts/hover-country.png'});
 await page.selectOption('#birth-grouping','regions');await expect(page.locator('#country-legend')).toContainText('Mayor subtotal regional');
 await page.reload();await expect(page.locator('#birth-grouping')).toHaveValue('regions');await expect(page.locator('#birth-mode')).toHaveValue('common');
 const dl=page.waitForEvent('download');await page.click('#birth-download');expect((await dl).suggestedFilename()).toBe('origen-predominante-2025-1280.csv');
 await page.selectOption('#birth-mode','share');await expect(page.locator('#birth-country')).toBeEnabled();
 await page.setViewportSize({width:390,height:844});await page.goto('countries/?mode=common&municipality=1280&country=SY');
 await expect(page.locator('#country-map')).toHaveAttribute('data-ready','true',{timeout:30000});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('.country-map-area').scrollIntoViewIfNeeded();await showHover(page,'#country-map');await page.screenshot({path:'tests/artifacts/hover-mobile.png'});
});
