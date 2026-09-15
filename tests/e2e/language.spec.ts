import {test,expect,type Page} from '@playwright/test';

async function chooseLanguage(page:Page,language:string){await page.locator('#language').click();await page.locator(`[data-language="${language}"]`).click();}

test('language selector preserves district and filters, translates both histories and navigation',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('./?lang=es&year=2026&county=01&municipality=0180&district=01803936');
 await expect(page.locator('[data-district-history]')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await chooseLanguage(page,'en');
 await expect(page.locator('html')).toHaveAttribute('lang','en');
 await expect(page.locator('[data-district-history]')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#county')).toHaveValue('01');
 await expect(page.locator('#municipality')).toHaveValue('0180');
 expect(new URL(page.url()).searchParams.get('district')).toBe('01803936');
 await expect(page.locator('[data-election-metric=winning_party]')).toHaveText('Leading party');
 await expect(page.locator('[data-history-votes] .timeline-heading')).toContainText('Votes');
 await expect(page.locator('[data-history-origin] .timeline-heading')).toContainText('Population background');
 await expect(page.locator('[data-history-origin] .series-title')).toContainText(['Sweden','Europe excluding Sweden','Rest of the world + unknown']);
 const first=page.locator('[data-history-votes] [data-series]').first();await first.click();await expect(first).toHaveAttribute('aria-pressed','false');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await page.screenshot({path:'tests/artifacts/language-en.png'});
 await page.click('nav a[data-route="evolution/"]');
 await expect(page.locator('#history-territory')).toHaveValue('0180');
 await expect(page.locator('#language')).toHaveAttribute('data-current-language','en');
 await chooseLanguage(page,'sv');
 await expect(page.locator('html')).toHaveAttribute('lang','sv');
 await expect(page.locator('.evolution-intro h2')).toHaveText('Utveckling');
 await expect(page.locator('#history-territory')).toHaveValue('0180');
 await page.click('nav a[data-route="countries/"]');
 await expect(page.locator('#language')).toHaveAttribute('data-current-language','sv');
 await expect(page.locator('#birth-municipality')).toHaveValue('0180');
 await page.selectOption('#birth-country','DE');
 await expect(page.locator('.country-selected-label')).toHaveText('Födda i Tyskland');
 await chooseLanguage(page,'en');
 await expect(page.locator('.country-selected-label')).toHaveText('Born in Germany');
 await expect(page.locator('#birth-country')).toHaveValue('DE');
 await page.goto('methodology/');
 await expect(page.locator('#language')).toHaveAttribute('data-current-language','en');
 await expect(page.locator('.methodology h1')).toHaveText('What this atlas measures');
 expect(errors).toEqual([]);
});

test('mobile language selector is visible, accessible and URL language overrides saved preference',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('./?lang=sv');
 await expect(page.locator('#map-left')).toHaveAttribute('data-ready','true');
 await expect(page.locator('#language')).toBeVisible();
 const box=await page.locator('#language').boundingBox();expect(box!.y).toBeLessThan(160);expect(box!.x+box!.width).toBeLessThanOrEqual(390);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('#language').click();
 await expect(page.locator('.language-menu [data-flag]')).toHaveCount(3);
 await page.screenshot({path:'tests/artifacts/language-sv-mobile.png'});
 await page.keyboard.press('Escape');await expect(page.locator('.language-picker')).not.toHaveAttribute('open','');
 await expect(page.locator('#language')).toBeFocused();
 await page.goto('./?lang=es');
 await expect(page.locator('#language')).toHaveAttribute('data-current-language','es');
 await expect(page.locator('[data-election-metric=winning_party]')).toHaveText('Partido dominante');
});
