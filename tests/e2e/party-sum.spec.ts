import {test,expect} from '@playwright/test';
import {gunzipSync} from 'node:zlib';
import {readFile} from 'node:fs/promises';
import Papa from 'papaparse';

test('combine parties updates the election map, share, CSV and URL without changing origin',async({page,request})=>{
 await page.setViewportSize({width:1366,height:768});
 const raw=await (await request.get('data/2026/districts.json.gz')).body();
 const rows=JSON.parse((raw[0]===0x1f?gunzipSync(raw):raw).toString());
 const sums=rows.map((d:any)=>100*(d.vote_S+d.vote_V)/d.valid_votes).sort((a:number,b:number)=>a-b);
 const quantile=(q:number)=>{const index=(sums.length-1)*q,low=Math.floor(index);return sums[low]+(sums[Math.ceil(index)]-sums[low])*(index-low);};
 expect(quantile(.95)-quantile(.05)).toBeGreaterThan(20);
 const expectedScale={min:Math.floor(quantile(.05)/5)*5,max:Math.ceil(quantile(.95)/5)*5};
 await page.goto('./?view=compare&lang=en&metric=born_rest_world_unknown_pct&party=S&municipality=0180');
 await expect(page.locator('#map-right')).toHaveAttribute('data-ready','true');
 const originScale=await page.locator('#map-left').getAttribute('data-scale-max');
 await page.locator('#compare-election').selectOption('custom_sum');
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.locator('[name=sum-party][value=V]').check();
 await expect(page.locator('#party-picker output')).toHaveText('S + V');
 await page.locator('#apply-party-sum').click();
 await expect(page.locator('#map-right')).toHaveAttribute('data-metric','pct_S+V');
 await expect(page.locator('#map-right')).toHaveAttribute('data-scale-min',String(expectedScale.min));
 await expect(page.locator('#map-right')).toHaveAttribute('data-scale-max',String(expectedScale.max));
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','born_rest_world_unknown_pct');
 await expect(page.locator('#map-left')).toHaveAttribute('data-scale-max',originScale!);
 await expect(page.locator('#right-legend')).toContainText('S + V');
 await expect(page.locator('#party')).toHaveValue('S+V');
 await expect(page.locator('.comparison-votes .selected-party-sum')).toContainText('S + V');
 expect(new URL(page.url()).searchParams.get('party')).toBe('S+V');
 const downloadPromise=page.waitForEvent('download');await page.locator('#download').click();
 const file=await downloadPromise,content=await readFile((await file.path())!,'utf8');
 const exported=Papa.parse<Record<string,string>>(content,{header:true,skipEmptyLines:true}).data;
 expect(exported.length).toBeGreaterThan(0);
 for(const d of exported){expect(d.municipality_code).toBe('0180');expect(Number(d['pct_S+V'])).toBeCloseTo(100*(Number(d.vote_S)+Number(d.vote_V))/Number(d.valid_votes),10);}
 await page.reload();await expect(page.locator('#map-right')).toHaveAttribute('data-metric','pct_S+V');
 await page.locator('#year').selectOption('2022');await expect(page.locator('#map-right')).toHaveAttribute('data-year','2022');
 await expect(page.locator('#map-right')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#compare-election')).toHaveValue('S+V');
 await page.screenshot({path:'.tools/party-sum-comparison.png'});
 for(const width of [1366,1024]){await page.setViewportSize({width,height:768});expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth)).toBe(true);}
 await page.locator('#compare-election').selectOption('winning_block');await expect(page.locator('#map-right')).toHaveAttribute('data-metric','winning_block');
 await page.locator('#compare-election').selectOption('S');await expect(page.locator('#map-right')).toHaveAttribute('data-metric','pct_S');
});

test('picker supports Swedish, keyboard cancellation, empty selection and mobile layout',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('./?lang=sv&view=electoral&metric=party&party=S');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await page.locator('#party').selectOption('custom_sum');
 await expect(page.locator('#party-picker-title')).toHaveText('Summera partier');
 await page.locator('[name=sum-party][value=S]').uncheck();
 await expect(page.locator('#apply-party-sum')).toBeDisabled();
 await page.locator('[name=sum-party][value=V]').check();await page.locator('[name=sum-party][value=MP]').check();
 await page.screenshot({path:'.tools/party-sum-picker-mobile.png'});
 const bounds=await page.locator('#party-picker').boundingBox();expect(bounds!.x).toBeGreaterThanOrEqual(0);expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(390);
 await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.locator('#party')).toHaveValue('S');
 await page.locator('#party').selectOption('custom_sum');await page.locator('[name=sum-party][value=V]').check();await page.locator('#apply-party-sum').click();
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','pct_S+V');
 await expect(page.locator('#legend')).toContainText('S + V');
});
