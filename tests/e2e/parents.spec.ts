import {test,expect} from '@playwright/test';
import {gunzipSync} from 'node:zlib';

test('origin definitions lead to observed municipal parental groups and retain correct denominators',async({page,request})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
 await page.goto('./?view=demography&metric=foreign_background_pct&municipality=0180');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});
 await page.locator('.indicator-help>.district-birth-notice>summary').click();
 await expect(page.locator('.indicator-help')).toContainText('No incluye');
 await page.locator('.definition-list>summary').click();await expect(page.locator('.definition-list dd').first()).toBeVisible();
 await expect(page.locator('.definition-list')).toContainText('Un progenitor nació en Suecia y el otro en el extranjero');
 await page.locator('.parents-link').click();
 await expect(page.locator('#country-map')).toHaveAttribute('data-ready','true',{timeout:30000});
 await expect(page.locator('#birth-grouping')).toHaveValue('parents');await expect(page.locator('#birth-municipality')).toHaveValue('0180');
 await expect(page.locator('#birth-country')).toHaveValue('PARENT_MIXED');await expect(page.locator('#birth-country option')).toHaveCount(4);
 await expect(page.locator('.parent-definition')).toContainText('un progenitor nacido en Suecia y otro en el extranjero');
 const response=await request.get('data/parents/background_2025.json.gz');const data=JSON.parse(gunzipSync(await response.body()).toString());
 const region=data.regions.find((r:{code:string})=>r.code==='0180');
 const expected=new Intl.NumberFormat('es-ES',{maximumFractionDigits:1}).format(100*region.counts.PARENT_MIXED/region.population)+' %';
 await expect(page.locator('.country-headline')).toHaveText(expected);
 await page.locator('#parents-notice>summary').click();await expect(page.locator('#parents-notice p').first()).toBeVisible();
 await page.getByText('Todos los orígenes',{exact:true}).click();await expect(page.locator('.country-table tbody tr')).toHaveCount(4);
 await page.locator('[data-birth-country=PARENT_BOTH_FOREIGN]').click();await expect(page.locator('#birth-country')).toHaveValue('PARENT_BOTH_FOREIGN');
 await page.reload();await expect(page.locator('#birth-grouping')).toHaveValue('parents');
 const dl=page.waitForEvent('download');await page.click('#birth-download');const download=await dl;expect(download.suggestedFilename()).toBe('padres-nacimiento-2025-0180.csv');
 const stream=await download.createReadStream();let csv='';for await(const chunk of stream!)csv+=chunk.toString();expect(csv).toContain('PARENT_MIXED');expect(csv).toContain('UtlSvBakgFinCKM');expect(csv).toContain('parental_background_code');
 await expect(page.locator('#country-map')).toHaveAttribute('data-ready','true',{timeout:30000});await expect.poll(async()=>Number(await page.locator('#country-map').getAttribute('data-features'))).toBeGreaterThan(0);await page.screenshot({path:'tests/artifacts/parents-desktop.png'});
 await page.selectOption('#birth-grouping','regions');await expect(page.locator('#birth-country option')).toHaveCount(10);await expect(page.locator('#parents-notice')).toBeHidden();
 await page.selectOption('#birth-mode','common');await page.selectOption('#birth-grouping','parents');await expect(page.locator('#birth-mode')).toHaveValue('share');
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'tests/artifacts/parents-mobile.png',fullPage:true});
 expect(errors).toEqual([]);
});

test('party and analytical block winners are directly selectable and shown together in district detail',async({page})=>{
 await page.goto('./?year=2026&municipality=0180');
 await expect(page.locator('#party')).toHaveValue('winning_party');await page.selectOption('#party',{label:'Bloque dominante'});
 await expect(page.locator('#map-left')).toHaveAttribute('data-metric','winning_block');await expect(page.locator('[data-election-metric=winning_block]')).toHaveAttribute('aria-pressed','true');
 await page.reload();await expect(page.locator('#metric')).toHaveValue('winning_block');await expect(page.locator('#party')).toHaveValue('winning_block');expect(new URL(page.url()).searchParams.get('party')).toBe('SD');
 await page.selectOption('#party','S');await expect(page.locator('#map-left')).toHaveAttribute('data-metric','party');await expect(page.locator('#party')).toHaveValue('S');
 await page.selectOption('#party',{label:'Partido dominante'});await expect(page.locator('#map-left')).toHaveAttribute('data-metric','winning_party');
 await page.fill('#search','01801506');await page.click('#search-results [data-district="01801506"]');
 await expect(page.locator('.election-winners')).toContainText('Partido más votado');await expect(page.locator('.election-winners')).toContainText('Bloque más votado');await expect(page.locator('.election-winners .party-badge')).toHaveCount(1);
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true',{timeout:30000});await expect(page.locator('#map-left')).toHaveAttribute('aria-busy','false');await page.screenshot({path:'tests/artifacts/election-winners.png'});await page.setViewportSize({width:390,height:844});await expect(page.locator('#party')).toBeVisible();await page.selectOption('#party','winning_block');await expect(page.locator('#map-left')).toHaveAttribute('data-metric','winning_block');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
