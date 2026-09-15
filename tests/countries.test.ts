import {describe,it,expect} from 'vitest';
import {countryShare,countryLabel,type BirthRegion} from '../src/utils/countries';
const region:BirthRegion={code:'x',name:'Test',level:'municipality',population:1000,counts:{SY:50,AF:null,ES:0,OVFOD:20,SE:700}};
describe('country proportions and suppressed counts',()=>{
 it('uses all residents as the denominator',()=>expect(countryShare(region,{code:'SY',name_sv:'Syrien',kind:'country'})).toBe(5));
 it('preserves grouped/missing countries instead of assigning zero',()=>{
  expect(countryShare(region,{code:'AF',name_sv:'Afghanistan',kind:'country'})).toBeNull();
  expect(countryShare(region,{code:'ES',name_sv:'Spanien',kind:'country'})).toBeNull();
 });
 it('keeps published grouped categories and Sweden distinct',()=>{
  expect(countryShare(region,{code:'OVFOD',name_sv:'övriga',kind:'group'})).toBe(2);
  expect(countryShare(region,{code:'SE',name_sv:'Sverige',kind:'country'})).toBe(70);
  expect(countryLabel({code:'ES',name_sv:'Spanien',kind:'country'})).toBe('España');
 });
});

it('labels geographic subtotals and retains the resident denominator',()=>{
 const group={code:'REG_ASIA',name_sv:'Asia',name_es:'Asia',kind:'region' as const};
 expect(countryLabel(group)).toBe('Asia');
 expect(countryShare({...region,counts:{REG_ASIA:120}},group)).toBe(12);
 expect(countryShare({...region,counts:{REG_ASIA:null}},group)).toBeNull();
});

it('parental birthplace groups retain published zero, missing values and their own population',()=>{
 const group={code:'PARENT_MIXED',name_sv:'test',name_es:'Un progenitor nacido fuera',kind:'parent'};
 expect(countryLabel(group)).toBe('Un progenitor nacido fuera');
 expect(countryShare({...region,population:250,counts:{PARENT_MIXED:25}},group)).toBe(10);
 expect(countryShare({...region,counts:{PARENT_MIXED:0}},group)).toBe(0);
 expect(countryShare({...region,counts:{PARENT_MIXED:null}},group)).toBeNull();
});
