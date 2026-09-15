import {test,expect} from '@playwright/test';
test('Spearman is primary, recalculates and is explained in all languages',async({page})=>{
 for(const [lang,label] of [['es','no paramétrica'],['en','nonparametric'],['sv','icke-parametrisk']]){
  await page.goto(`./analysis/?year=2026&analysisX=born_rest_world_unknown_pct&party=S&lang=${lang}`);
  const primary=page.locator('.stat-strip>div').first();
  await expect(primary).toHaveAttribute('data-stat','spearman');
  await expect(primary).toContainText(label);
  expect((await primary.locator('b').innerText()).replace(',','.')).toBe('0.517');
  await expect(page.locator('.correlation-caption')).toContainText('OLS');
  expect(await page.locator('.scatter circle').count()).toBe(6312);
 }
 await page.goto('./analysis/?year=2026&analysisX=born_rest_world_unknown_pct&party=V&lang=en');
 await expect(page.locator('[data-stat=spearman] b')).toHaveText('0.785');
 const download=page.locator('.plot-downloads a').first();
 await expect(download).toHaveAttribute('href',/v8-spearman\.png$/);
 const response=await page.request.get((await download.getAttribute('href'))!);expect(response.ok()).toBe(true);
 expect(response.headers()['content-type']).toContain('image/png');
 await page.locator('#point-size').selectOption('votes');
 await expect(page.locator('[data-stat=spearman] b')).toHaveText('0.785');
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'.tools/spearman-mobile.png',fullPage:true});
 await page.setViewportSize({width:1366,height:900});
 await page.screenshot({path:'.tools/spearman-desktop.png',fullPage:true});
 await page.goto('./methodology/?lang=en');
 await expect(page.locator('article')).toContainText('Spearman ρ is the primary correlation');
 await expect(page.locator('article')).toContainText('average ranks for ties');
});
