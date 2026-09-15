import {describe,it,expect} from 'vitest';
import {percentageScale,metricScale,scaleStops,legend} from '../src/maps/palette';
import type {District,State} from '../src/types';
describe('national indicator scales',()=>{
 it('keeps a rare high outlier from flattening the other districts without changing values',()=>{
  const values=[...Array.from({length:100},(_,i)=>i/10),80],copy=[...values],range=percentageScale(values);
  expect(range.min).toBe(0);expect(range.max).toBe(10);expect(range.highClipped).toBe(true);expect(values).toEqual(copy);
  expect(scaleStops(range)).toHaveLength(11);expect(scaleStops(range).at(-1)![0]).toBe(10);
 });
 it('handles empty, constant and tiny percentage ranges with finite ascending stops',()=>{
  for(const values of [[],[0,0],[50,50],[100,100],[.01,.02,.03]]){
   const domain=percentageScale(values),stops=scaleStops(domain);
   expect(domain.min).toBeLessThan(domain.max);expect(domain.min).toBeGreaterThanOrEqual(0);expect(domain.max).toBeLessThanOrEqual(100);
   expect(stops.every(([x],i)=>Number.isFinite(x)&&(!i||x>stops[i-1][0]))).toBe(true);
  }
 });
 it('uses the selected indicator in its legend and marks saturated ends',()=>{
  const rows=Array.from({length:101},(_,i)=>({pct_V:i===100?80:i/10,pct_S:30+i/10}) as unknown as District);
  const state={view:'electoral',metric:'party',party:'V'} as State;
  const domain=metricScale(rows,'pct_V');expect(domain.max).toBe(10);
  expect(legend(state,rows)).toContain('data-scale-max="10"');expect(legend(state,rows)).toContain('≥ ');
  expect(metricScale(rows,'pct_S').max).toBeGreaterThan(domain.max);
 });
});
