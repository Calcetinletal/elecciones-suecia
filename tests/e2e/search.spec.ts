import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import Papa from 'papaparse';

test('search filters municipalities and frames municipalities or districts on both maps',async({page})=>{
 await page.setViewportSize({width:1366,height:768});
 await page.goto('./?view=compare&year=2026&lang=en');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#map-right')).toHaveAttribute('data-ready','true');
 await page.locator('#search').fill('Stockholm');
 await page.locator('#search').press('Enter');
 await expect(page.locator('#municipality')).toHaveValue('0180');
 await expect(page.locator('#county')).toHaveValue('01');
 await expect(page.locator('#map-count')).toContainText('606 districts');
 for(const id of ['#map-left','#map-right']){
  await expect.poll(async()=>Number(await page.locator(id).getAttribute('data-zoom'))).toBeGreaterThan(8);
  expect(Number(await page.locator(id).getAttribute('data-lat'))).toBeCloseTo(59.33,1);
 }
 const downloadEvent=page.waitForEvent('download');await page.locator('#download').click();
 const download=await downloadEvent;
 const csv=Papa.parse<Record<string,string>>(await readFile((await download.path())!,'utf8'),{header:true,skipEmptyLines:true}).data;
 expect(csv).toHaveLength(606);expect(new Set(csv.map(d=>d.municipality_code))).toEqual(new Set(['0180']));
 // Select an urban district by keyboard; it must fit its own boundary, not the municipality.
 await page.locator('#search').fill('01801507');
 await page.locator('#search').press('ArrowDown');
 await expect(page.locator('#search-results button').first()).toBeFocused();
 await page.keyboard.press('Enter');
 await expect(page.locator('#panel-content')).toContainText('01801507');
 await expect.poll(()=>Number(new URL(page.url()).searchParams.get('zoom'))).toBeGreaterThan(13);
 for(const id of ['#map-left','#map-right'])await expect.poll(async()=>Number(await page.locator(id).getAttribute('data-zoom'))).toBeGreaterThan(13);
 for(const key of ['data-lng','data-lat','data-zoom'])expect(await page.locator('#map-right').getAttribute(key)).toBe(await page.locator('#map-left').getAttribute(key));
 // Resizing the comparison and opening history must not undo the search camera.
 await page.setViewportSize({width:1024,height:768});
 await expect(page.locator('#panel-content [data-district-history]')).toHaveAttribute('data-ready','true');
 expect(Number(new URL(page.url()).searchParams.get('zoom'))).toBeGreaterThan(13);
 await page.screenshot({path:'.tools/search-district-compare.png'});
 // A result outside the current filters replaces the old territorial scope.
 await page.locator('#search').fill('Ludvika');
 await page.locator('#search-results [data-municipality="2085"]').click();
 await expect(page.locator('#municipality')).toHaveValue('2085');
 await expect(page.locator('#county')).toHaveValue('20');
 await expect(page.locator('#map-count')).toContainText('15 districts');
 expect(new URL(page.url()).searchParams.has('district')).toBe(false);
 await expect.poll(async()=>Number(await page.locator('#map-left').getAttribute('data-lat'))).toBeGreaterThan(60);
 await expect.poll(async()=>Number(await page.locator('#map-left').getAttribute('data-zoom'))).toBeLessThan(10);
 const camera=new URL(page.url()).searchParams;
 await page.reload();await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#municipality')).toHaveValue('2085');
 for(const key of ['lng','lat','zoom'])expect(new URL(page.url()).searchParams.get(key)).toBe(camera.get(key));
});

test('district search from the national single map selects its municipality and zooms locally',async({page})=>{
 await page.goto('./?year=2026&lang=en');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await page.locator('#search').fill('01801507');await page.locator('#search').press('Enter');
 await expect(page.locator('#municipality')).toHaveValue('0180');
 await expect.poll(()=>Number(new URL(page.url()).searchParams.get('zoom'))).toBeGreaterThan(13);
 await expect(page.locator('#map-count')).toContainText('606 districts');
 await page.locator('#search').fill('Stockholm');await page.locator('#search').press('ArrowDown');
 await page.keyboard.press('ArrowUp');await expect(page.locator('#search')).toBeFocused();
 await page.keyboard.press('Escape');await expect(page.locator('#search-results button')).toHaveCount(0);
});
