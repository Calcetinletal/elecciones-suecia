import {describe,it,expect} from 'vitest';
import {readState,routeUrl} from '../src/utils/state';
import {clearMunicipality,comparisonMapState} from '../src/utils/comparison-maps';
import {aggregateSocio,socioValue} from '../src/utils/socio';
import {districtSocioSeries} from '../src/components/socio-history';
import {historyScale} from '../src/utils/history-scale';
import type {District} from '../src/types';
describe('historical rates and comparison scope',()=>{
 it('fits narrow historical changes while retaining every observation and a zero option',()=>{
  const fitted=historyScale([80,81,82],'%');
  expect(fitted.bottom).toBeGreaterThan(75);expect(fitted.bottom).toBeLessThanOrEqual(80);expect(fitted.top).toBeGreaterThanOrEqual(82);expect(fitted.top-fitted.bottom).toBeLessThan(5);
  expect(historyScale([80,81,82],'%',true).bottom).toBe(0);
  for(const [values,unit] of [[[0,0],'%'],[[100,100],'%'],[[1000000],'SEK'],[[-5000,25000],'SEK'],[[],'%']] as [number[],string][]){
   const range=historyScale(values,unit);expect(range.top).toBeGreaterThan(range.bottom);expect(range.ticks.every(Number.isFinite)).toBe(true);
   for(const value of values){expect(value).toBeGreaterThanOrEqual(range.bottom);expect(value).toBeLessThanOrEqual(range.top);}
  }
 });
 it('marks reused-code history as unverified even when the break is after the final income year',()=>{
  const old={district_id:'x',district_name:'Old district',election_year:2022} as unknown as District;
  const current={...old,district_name:'Changed district',election_year:2026};
  const archive={editions:{2022:[old],2026:[current]},links:{},birth:{}};
  const data={area:{},districts:{2022:{x:{income:[{year:2024,n:2000000,d:10}]}}}};
  const points=districtSocioSeries(current,archive,data,'income');
  expect(points).toHaveLength(1);expect(points[0].geometry).toBe(2022);expect(points[0].comparable).toBe(false);expect(socioValue(points[0],1)).toBe(200000);
 });
 it('all municipalities clears the implicit county and district',()=>{const s=readState('?county=01&municipality=0180&district=01801507');clearMunicipality(s);expect([s.county,s.municipality,s.district]).toEqual(['','','']);});
 it('combines counts and denominators, with no partial or missing-rate substitution',()=>{
  const p=aggregateSocio([{year:2020,n:20,d:40},{year:2020,n:30,d:100}],2020);
  expect(socioValue(p,100)).toBeCloseTo(100*50/140);
  expect(socioValue(aggregateSocio([{year:2020,n:20,d:40},undefined],2020),100)).toBeNull();
  expect(socioValue(aggregateSocio([{year:2020,n:40,d:1},{year:2020,n:100,d:1}],2020,true),1)).toBe(140);
 });
 it('preserves four independent map indicators and custom party sums in shared URLs',()=>{
  const s=readState('?view=compare&mapCount=4&party=S%2BV&map3=vote%3AM%2BKD&map4=socio_senior_pct&metric=born_rest_world_unknown_pct');
  expect(comparisonMapState(s,0).metric).toBe('born_rest_world_unknown_pct');expect(comparisonMapState(s,1).party).toBe('S+V');
  expect(comparisonMapState(s,2).party).toBe('M+KD');expect(comparisonMapState(s,3).metric).toBe('socio_senior_pct');
  expect(readState(new URL(routeUrl('',s),'https://example.test').search)).toEqual(s);
  expect(readState('?mapCount=100&map3=invalid').mapCount).toBe(2);
 });
});
