import {describe,it,expect,vi,afterEach} from 'vitest';
import catalog from '../src/i18n/messages.txt?raw';
import {translate} from '../src/i18n';
import {readLanguage,languageUrl} from '../src/i18n/language';
import {readState} from '../src/utils/state';
afterEach(()=>vi.unstubAllGlobals());
describe('languages',()=>{
 it('has complete English and Swedish entries with unique source keys',()=>{
  const entries=catalog.replace(/^\uFEFF/,'').split(/\r?\n/).filter(x=>x.trim()&&!x.trimStart().startsWith('#')).map(x=>x.split('|||'));
  expect(entries.every(e=>e.length===3&&e.every(x=>x.trim()))).toBe(true);
  expect(new Set(entries.map(e=>e[0])).size).toBe(entries.length);
 });
 it('translates complete definitions before fragments without changing numbers or names',()=>{
  expect(translate('Límites 2026 · Hägersten 36 Västberga Ö (01803936)','en')).toBe('Boundaries 2026 · Hägersten 36 Västberga Ö (01803936)');
  expect(translate('Europa excepto Suecia ≈ 18.5 %','sv')).toBe('Europa utom Sverige ≈ 18.5 %');
  expect(translate('Nacidos en Suecia · un padre fuera','en')).toBe('Sweden-born · one parent born abroad');
  expect(translate('Ciudadanía extranjera¹ ≈','en')).toBe('Foreign citizenship¹ ≈');
  expect(translate('2010. Consulta los distritos antiguos en el archivo.','en')).toBe('2010. See earlier districts in the archive.');
  expect(translate('Nacidos en Suecia','es')).toBe('Nacidos en Suecia');
 });
 it('uses explicit language, then legacy locale, then a saved preference; ignores invalid codes',()=>{
  vi.stubGlobal('localStorage',{getItem:()=> 'sv'});
  expect(readLanguage('?lang=en&locale=es-ES')).toBe('en');
  expect(readLanguage('?locale=en-GB')).toBe('en');
  expect(readLanguage('')).toBe('sv');
  expect(readLanguage('?lang=constructor')).toBe('sv');
  expect(readState('?lang=en').locale).toBe('en-GB');
 });
 it('retains all view parameters and hashes when switching language',()=>{
  vi.stubGlobal('location',{href:'https://example.org/atlas/'});
  const url=new URL(languageUrl('evolution/?scope=district&district=01803936&year=2022&locale=es-ES#chart','sv'));
  expect(url.pathname).toBe('/atlas/evolution/');expect(url.hash).toBe('#chart');expect(url.searchParams.get('district')).toBe('01803936');expect(url.searchParams.get('year')).toBe('2022');expect(url.searchParams.get('locale')).toBe('sv-SE');expect(url.searchParams.get('lang')).toBe('sv');
 });
});
