import {test,expect} from '@playwright/test';
test('comparison shows every party and birthplace group with both maps without scrolling',async({page})=>{
 for(const [width,height,lang] of [[1366,768,'es'],[1024,768,'en'],[1440,900,'sv']] as const){
  await page.setViewportSize({width,height});
  for(const district of ['', '01801507']){
   await page.goto(`./?view=compare&municipality=0180&district=${district}&lang=${lang}`);
   await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
   await expect(page.locator('#map-right')).toHaveAttribute('data-ready','true');
   if(district){
    await expect(page.locator('#panel-content [data-district-history]')).toHaveAttribute('data-ready','true');
    await expect(page.locator('#panel-content [data-history-votes] .series-card')).toHaveCount(9);
    await expect(page.locator('#panel-content [data-history-origin] .series-card')).toHaveCount(3);
   }else{await expect(page.locator('.comparison-party')).toHaveCount(9);await expect(page.locator('.comparison-origin-list>div')).toHaveCount(3);}
   const bounds=await page.locator('.comparison-data, #map-left, #map-right, .comparison-party, .comparison-origin-list>div, #panel-content .timeline-svg, #panel-content .series-card, #comparison-detail').evaluateAll(els=>els.map(el=>{const r=el.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right}}));
   for(const r of bounds){expect(r.top).toBeGreaterThanOrEqual(0);expect(r.bottom).toBeLessThanOrEqual(height);expect(r.left).toBeGreaterThanOrEqual(0);expect(r.right).toBeLessThanOrEqual(width);}
   expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   expect(await page.locator('.side-panel').evaluate(el=>el.scrollHeight<=el.clientHeight)).toBe(true);
  }
 }
 await page.locator('#comparison-detail').click();
 await expect(page.locator('#comparison-dialog')).toBeVisible();
 await expect(page.locator('#comparison-dialog [data-district-history]')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#comparison-dialog [data-history-votes]')).toBeVisible();
 await expect(page.locator('#comparison-dialog [data-history-origin]')).toBeVisible();
 await page.keyboard.press('Escape');await expect(page.locator('#comparison-dialog')).toHaveCount(0);
 await expect(page.locator('#panel-content [data-history-votes] .timeline-svg')).toBeVisible();
 await expect(page.locator('#panel-content [data-history-origin] .timeline-svg')).toBeVisible();
 const series=page.locator('#panel-content [data-history-votes] [data-series=V]');await series.click();await expect(series).toHaveAttribute('aria-pressed','false');
 await expect(page.locator('#panel-content [data-history-votes] [data-line-series=V]')).toHaveCount(0);
 await page.locator('#close-district').click();await expect(page.locator('.comparison-scope')).toContainText('Stockholm');
});
