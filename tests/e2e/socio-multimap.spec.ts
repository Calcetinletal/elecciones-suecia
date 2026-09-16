import {test,expect} from '@playwright/test';
test('all municipalities restores the entire country after a search',async({page})=>{
 await page.goto('./?view=compare&mapCount=4&lang=en');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});
 await page.locator('#search').fill('Stockholm');await page.locator('#search').press('Enter');
 await expect(page.locator('#map-count')).toContainText('606 districts');
 await page.locator('#municipality').selectOption('');
 await expect(page.locator('#county')).toHaveValue('');await expect(page.locator('#map-count')).toContainText('6,312 districts');
 for(const id of ['map-left','map-right','map-3','map-4'])await expect.poll(async()=>Number(await page.locator('#'+id).getAttribute('data-zoom'))).toBeLessThan(6);
});
test('four maps stay synchronised, retain independent indicators and fit the desktop viewport',async({page})=>{
 await page.setViewportSize({width:1366,height:768});
 await page.goto('./?view=compare&municipality=0180&lang=en&party=S%2BV');
 await expect(page.locator('#map-right')).toHaveAttribute('data-ready','true',{timeout:30000});
 await page.locator('#map-number').selectOption('4');await expect(page.locator('.map')).toHaveCount(4);
 await expect(page.locator('#map-4')).toHaveAttribute('data-ready','true',{timeout:30000});
 await expect(page.locator('#map-3')).toHaveAttribute('data-metric','mean_net_income');
 await page.locator('[data-extra-map="2"]').selectOption('vote:S+V');await expect(page.locator('#map-3')).toHaveAttribute('data-metric','pct_S+V');
 await page.locator('[data-extra-map="3"]').selectOption('socio_senior_pct');await expect(page.locator('#map-4')).toHaveAttribute('data-metric','socio_senior_pct');
 await expect(page.locator('#legend-4')).toContainText('Age 65 and over');
 for(const width of [1366,1024]){
  await page.setViewportSize({width,height:768});
  expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const sizes=await page.locator('.map').evaluateAll(els=>els.map(el=>el.getBoundingClientRect().toJSON()));for(const size of sizes){expect(size.width).toBeGreaterThan(150);expect(size.height).toBeGreaterThan(75);expect(size.bottom).toBeLessThanOrEqual(768);}
 }
 await page.setViewportSize({width:1366,height:768});
 await expect.poll(()=>page.locator('.map').evaluateAll(els=>els.every(el=>Math.abs(el.getBoundingClientRect().width-el.querySelector('canvas')!.getBoundingClientRect().width)<1))).toBe(true);
 await page.screenshot({path:'.tools/four-maps.png'});
 await page.reload();await expect(page.locator('#map-4')).toHaveAttribute('data-metric','socio_senior_pct');
 await page.locator('#map-number').selectOption('3');await expect(page.locator('.map')).toHaveCount(3);
 await page.locator('#map-number').selectOption('2');await expect(page.locator('.map')).toHaveCount(2);
});
test('separate historical menu has income, social and demographic series with actual years and CSV',async({page})=>{
 await page.goto('./?view=compare&municipality=0180&lang=en&district=01801507');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});
 await page.locator('#socio-history-menu>summary').click();
 const host=page.locator('.socio-history-content');await expect(host).toHaveAttribute('data-ready','true',{timeout:30000});
 await expect(host).toHaveAttribute('data-scope','district');await expect(host.locator('polyline')).toBeVisible();
 expect(Number(await host.getAttribute('data-observations'))).toBeGreaterThan(5);
 await expect(host.locator('.socio-universe')).toContainText('2024 prices');
 await host.locator('[data-socio-metric]').selectOption('employment');await expect(host.locator('.socio-universe')).toContainText('20–64');
 expect(Number(await host.getAttribute('data-observations'))).toBeGreaterThan(2);
 await host.locator('[data-socio-metric]').selectOption('senior');await expect(host.locator('.socio-readout span')).toContainText('2025');
 const download=page.waitForEvent('download');await host.locator('[data-socio-download]').click();expect((await download).suggestedFilename()).toContain('senior');
 await host.locator('[data-socio-metric]').selectOption('income');await page.screenshot({path:'.tools/socio-history-district.png'});
 await host.locator('[data-socio-close]').click();await expect(page.locator('#socio-history-menu')).not.toHaveAttribute('open','');
 await page.goto('./?view=compare&municipality=0180&lang=sv');await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});
 await page.locator('#socio-history-menu>summary').click();await expect(page.locator('.socio-history-content')).toHaveAttribute('data-ready','true',{timeout:30000});
 await expect(page.locator('.socio-history-content')).toHaveAttribute('data-observations','14');
 await expect(page.locator('.socio-readout span')).toHaveText('2024');
 await page.setViewportSize({width:390,height:844});const box=await page.locator('.socio-history-content').boundingBox();expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(390);await page.screenshot({path:'.tools/socio-history-mobile.png'});
});
