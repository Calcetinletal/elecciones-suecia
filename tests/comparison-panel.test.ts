import {describe,it,expect} from 'vitest';
import {comparisonValues} from '../src/components/comparison-panel';
import type {District} from '../src/types';
const row=(values:Record<string,unknown>)=>values as unknown as District;
describe('comparison data uses compatible denominators',()=>{
 it('aggregates birthplace counts rather than averaging district percentages',()=>{
  const result=comparisonValues([
   row({birth_regions_population:100,born_sweden_count:80,born_europe_ex_sweden_count:10,born_rest_world_unknown_count:10}),
   row({birth_regions_population:900,born_sweden_count:450,born_europe_ex_sweden_count:90,born_rest_world_unknown_count:360}),
  ],'votes');
  expect(result.population).toBe(1000);expect(result.origins.map(g=>g.pct)).toEqual([53,10,37]);
 });
 it('uses the same complete district set for all birthplace groups and preserves missing data',()=>{
  const rows=[row({birth_regions_population:100,born_sweden_count:80,born_europe_ex_sweden_count:10,born_rest_world_unknown_count:10}),row({birth_regions_population:900,born_sweden_count:450,born_europe_ex_sweden_count:90,born_rest_world_unknown_count:null})];
  const result=comparisonValues(rows,'votes');expect(result.birthDistricts).toBe(1);expect(result.population).toBe(100);expect(result.origins.map(g=>g.pct)).toEqual([80,10,10]);
  expect(comparisonValues([rows[1]],'votes').origins.every(g=>g.pct===null)).toBe(true);
 });
 it('respects vote weighting and weights demographic measures by residents',()=>{
  const rows=[row({valid_votes:100,pct_S:10,population:100,foreign_background_pct:10}),row({valid_votes:900,pct_S:50,population:300,foreign_background_pct:30})];
  expect(comparisonValues(rows,'votes').votes.find(p=>p.id==='S')?.pct).toBe(46);
  expect(comparisonValues(rows,'equal').votes.find(p=>p.id==='S')?.pct).toBe(30);
  expect(comparisonValues(rows,'votes').foreignBackground).toBe(25);
 });
});
