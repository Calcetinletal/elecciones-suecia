import {test,expect} from '@playwright/test';
import {gunzipSync} from 'node:zlib';

test('refresh shows territorial and late collection coverage and uses the same snapshot in history',async({page,request})=>{
 const manifest=await (await request.get('data/manifest.json')).json();
 const edition=manifest.years.find((r:{year:number})=>r.year===2026);
 expect(edition.reported_unit_count).toBe(edition.reported_district_count+edition.reported_non_geographic_count);
 const index=await (await request.get('data/history/index.json')).json();
 expect(index.source_updated_2026).toBe(edition.source_updated_at);
 const raw=await (await request.get('data/history/00.json.gz')).body();
 const history=JSON.parse((raw[0]===0x1f?gunzipSync(raw):raw).toString());
 const latest=history.votes.at(-1);
 expect(latest.reported_units).toBe(edition.reported_unit_count);
 expect(latest.expected_units).toBe(edition.reporting_unit_count);
 await page.goto('./?view=compare&lang=en');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await expect(page.locator('.release-notice summary')).toContainText('Late-vote collection: 175 / 314');
 await expect(page.locator('.release-notice summary')).toContainText('16/09 15:15');
 await page.goto('./evolution/?lang=en');
 await expect(page.locator('#votes-note')).toContainText(edition.source_updated_at.replace('T',' '));
 await expect(page.locator('#votes-note')).toContainText('6,487');
 await page.screenshot({path:'.tools/election-refresh-history.png'});
});
