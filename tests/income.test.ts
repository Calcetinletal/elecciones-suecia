import {describe,it,expect} from 'vitest';
import {aggregateIncome,metricAmount} from '../src/utils/income';
import {incomeScale,legend} from '../src/maps/palette';
import {readState} from '../src/utils/state';
import type {District,State} from '../src/types';
describe('income units and aggregation',()=>{
 it('weights area summaries by the income population, excludes missing, keeps zero',()=>{
  const rows=[{mean_net_income:100000,income_population:100,income_total_sek:10000000},{mean_net_income:300000,income_population:900,income_total_sek:270000000},{mean_net_income:null,income_population:5000,income_total_sek:null},{mean_net_income:0,income_population:100,income_total_sek:0}] as unknown as District[];
  expect(aggregateIncome(rows)).toEqual({mean:280000000/1100,people:1100,districts:3});
 });
 it('uses a currency scale above 100 and retains outliers in data',()=>{
  const values=[...Array.from({length:100},(_,i)=>150000+i*2000),2800000],copy=[...values],range=incomeScale(values);
  expect(range.max).toBeGreaterThan(100000);expect(range.max).toBeLessThan(2800000);expect(range.highClipped).toBe(true);expect(values).toEqual(copy);
  for(const a of [[],[0,0],[-100,100],[200000,200000]])expect(incomeScale(a).max).toBeGreaterThan(incomeScale(a).min);
 });
 it('labels currency and preserves an independently selectable analysis axis',()=>{
  const s=readState('?view=compare&metric=mean_net_income&analysisX=mean_net_income');expect(s.metric).toBe('mean_net_income');expect(s.analysisX).toBe('mean_net_income');
  expect(metricAmount(300000,s.metric)).toContain('SEK/año');expect(metricAmount(300000,s.metric)).not.toContain('%');
  const html=legend({...s,view:'demography'} as State,[{mean_net_income:300000,income_year:2024}] as unknown as District[]);
  expect(html).toContain('2024');expect(html).toContain('SEK/año');expect(html).not.toContain('300.000 %');
 });
});
