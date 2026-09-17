import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
const manifest=JSON.parse(readFileSync('public/data/manifest.json','utf8'));
function expected(year:number,municipality=''){
 const entry=manifest.years.find((y:{year:number})=>y.year===year),rows=JSON.parse(gunzipSync(readFileSync('public/data/'+entry.table)).toString());
 const known=rows.filter((d:any)=>(!municipality||d.municipality_code===municipality)&&d.election_reported!==false&&typeof d.valid_votes==='number'&&d.valid_votes>0);
 return {count:known.length,votes:known.reduce((n:number,d:any)=>n+d.valid_votes,0)};
}
test('cartogram preserves all district votes, changes representation and restores nationwide scope',async({page})=>{
 test.setTimeout(180000);const errors:string[]=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.message)});await page.setViewportSize({width:1366,height:768});
 await page.goto('./?view=cartogram&lang=en');const stage=page.locator('.cartogram-stage');await expect(stage).toHaveAttribute('data-ready','true',{timeout:90000});
 const all=expected(2026);await expect(stage).toHaveAttribute('data-node-count','290');await expect(stage).toHaveAttribute('data-unit','municipality');await expect(stage).toHaveAttribute('data-vote-total',String(all.votes));await expect(page.locator('.cartogram-results')).toHaveAttribute('data-vote-total',String(all.votes));
 expect(Number(await stage.getAttribute('data-max-overlap'))).toBeLessThan(.001);
 expect(Number(await stage.getAttribute('data-layout-span'))).toBeLessThan(1500);
 await expect(stage).toHaveAttribute('data-layout','geographic');
 for(const mode of ['geography','voters','shares']){await page.locator(`[data-cartogram-mode="${mode}"]`).click();await expect(stage).toHaveAttribute('data-mode',mode);await expect(stage).toHaveAttribute('data-animating','false',{timeout:20000});await expect(stage).toHaveAttribute('data-vote-total',String(all.votes));await page.screenshot({path:'.tools/cartogram-'+mode+'.png'});}
 expect((await stage.boundingBox())!.height).toBeGreaterThan(400);await expect(page.locator('#cartogram-reference-canvas')).toBeVisible();
 await page.locator('#cartogram-expand').click();await expect(page.locator('.cartogram-expanded')).toBeVisible();await page.screenshot({path:'.tools/cartogram-expanded.png'});await page.keyboard.press('Escape');await expect(page.locator('.cartogram-expanded')).toHaveCount(0);
 await page.locator('#cartogram-unit').selectOption('district');await expect(stage).toHaveAttribute('data-node-count',String(all.count),{timeout:60000});await expect(stage).toHaveAttribute('data-vote-total',String(all.votes));
 await page.locator('.cartogram-filters').evaluate((el:HTMLDetailsElement)=>el.open=true);
 await page.locator('#search').fill('Stockholm');await page.locator('#search').press('Enter');await expect(stage).toHaveAttribute('data-ready','true',{timeout:60000});await expect(stage).toHaveAttribute('data-node-count',String(expected(2026,'0180').count));
 await page.locator('.cartogram-filters').evaluate((el:HTMLDetailsElement)=>el.open=true);
 await page.locator('#municipality').selectOption('');await expect(stage).toHaveAttribute('data-node-count',String(all.count),{timeout:60000});await expect(page.locator('#county')).toHaveValue('');
 await page.locator('#year').selectOption('2022');await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-vote-total',String(expected(2022).votes),{timeout:90000});await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-node-count',String(expected(2022).count));
 expect(errors).toEqual([]);
});
test('cartogram works with party sums, district selection, mobile and other atlas views',async({page})=>{
 await page.goto('./?view=cartogram&municipality=0180&lang=es&party=S%2BV&metric=party');await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-ready','true',{timeout:60000});
 await expect(page.locator('#cartogram-color-key')).toContainText('S + V');
 await page.locator('.cartogram-filters').evaluate((el:HTMLDetailsElement)=>el.open=true);
 await page.locator('#search').fill('01801507');await page.locator('#search').press('Enter');await expect(page.locator('.cartogram-results h2')).toContainText('Katarina');
 await page.locator('#comparison-detail').click();await expect(page.locator('#comparison-dialog')).toBeVisible();await page.keyboard.press('Escape');
 await page.locator('#close-district').click();await expect(page.locator('.cartogram-results h2')).toHaveText('Stockholm');
 await page.locator('[data-cartogram-mode="shares"]').click();await page.reload();await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-mode','shares',{timeout:60000});
 await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-ready','true',{timeout:60000});await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-animating','false',{timeout:15000});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'.tools/cartogram-mobile.png',fullPage:true});
 await page.setViewportSize({width:1024,height:768});expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('[data-view="compare"]').click();await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});await expect(page.locator('.cartogram-stage')).toHaveCount(0);
 await page.locator('.cartogram-entry').click();await expect(page.locator('.cartogram-stage')).toHaveAttribute('data-ready','true',{timeout:60000});
});
