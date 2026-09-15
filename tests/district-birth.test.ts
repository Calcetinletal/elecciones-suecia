import {describe,it,expect} from 'vitest';
import {readState} from '../src/utils/state';
import {value} from '../src/utils/data';
import {label} from '../src/maps/palette';
import type {District} from '../src/types';
describe('district birth-region comparison state',()=>{
 it('keeps the selected demographic category across shared comparison URLs',()=>{
  const state=readState('?view=compare&year=2026&metric=born_europe_ex_sweden_pct&party=S');
  expect(state.metric).toBe('born_europe_ex_sweden_pct');
  expect(label(state)).toContain('Europa excepto Suecia');
  expect(value({born_europe_ex_sweden_pct:14,foreign_background_pct:50} as unknown as District,state)).toBe(14);
 });
 it('normalizes older comparison URLs to the previous demographic default',()=>{
  expect(readState('?view=compare&metric=party').metric).toBe('foreign_background_pct');
 });
 it('retains unknown birthplace in the category label and handles missing estimates',()=>{
  const state=readState('?view=demography&metric=born_rest_world_unknown_pct');
  expect(label(state)).toContain('desconocido');
  expect(value({born_rest_world_unknown_pct:null} as unknown as District,state)).toBeNull();
 });
});

