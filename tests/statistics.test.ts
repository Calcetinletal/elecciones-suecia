import {describe,it,expect} from 'vitest';
import {pearson,spearman,ranks,linear,quantile,regression} from '../src/analysis/statistics';
import {readState} from '../src/utils/state';
import {weightedMean,filtered,turnout} from '../src/utils/data';
import type {District} from '../src/types';
describe('descriptive statistics',()=>{
 it('correlates positive and negative sequences',()=>{expect(pearson([1,2,3],[2,4,6])).toBeCloseTo(1);expect(pearson([1,2,3],[6,4,2])).toBeCloseTo(-1);});
 it('does not invent correlation for constants or tiny samples',()=>{expect(pearson([1,1,1],[2,4,6])).toBeNull();expect(pearson([1,2],[3,4])).toBeNull();expect(linear([1,1,1],[2,4,6])).toBeNull();});
 it('averages tied ranks',()=>{expect(ranks([40,10,10,20])).toEqual([4,1.5,1.5,3]);expect(spearman([1,2,2,4],[2,4,4,8])).toBeCloseTo(1);});
 it('fits a known line',()=>{expect(linear([1,2,3,4],[5,8,11,14])).toEqual({slope:3,intercept:2});});
 it('uses interpolated quantiles',()=>{expect(quantile([0,10,20,30],.5)).toBe(15);expect(quantile([],0.5)).toBeNull();});
 it('fits a full-rank multiple regression',()=>{const x=[[0,1],[1,0],[2,3],[3,1],[4,2],[5,0],[6,4]],y=x.map(([a,b])=>5+2*a-3*b);const result=regression(x,y)!;expect(result.r2).toBeCloseTo(1);expect(result.coefficients[1]/result.sd[0]).toBeCloseTo(2);expect(result.coefficients[2]/result.sd[1]).toBeCloseTo(-3);});
 it('rejects singular design matrices',()=>{expect(regression([[1,2],[2,4],[3,6],[4,8],[5,10],[6,12]],[2,4,6,8,10,12])).toBeNull();});
});
describe('missing data and state',()=>{
 const rows=[{district_id:'a',foreign_background_pct:0,pct_S:0,valid_votes:10,county_code:'01',municipality_code:'0114',coverage_quality:'high_coverage'},{district_id:'b',foreign_background_pct:100,pct_S:100,valid_votes:30,county_code:'02',municipality_code:'0200',coverage_quality:'high_coverage'},{district_id:'c',foreign_background_pct:null,pct_S:null,valid_votes:1000}] as unknown as District[];
 it('keeps zero, excludes null and uses the valid denominator',()=>{expect(weightedMean(rows,'pct_S','votes')).toBe(75);expect(weightedMean(rows,'pct_S','equal')).toBe(50);});
 it('sanitizes shareable state',()=>{const s=readState('?year=2026&party=FAKE&zoom=NaN&view=bivariate&locale=sv-SE&lng=999');expect(s.year).toBe(2026);expect(s.party).toBe('SD');expect(s.zoom).toBe(4.2);expect(s.lng).toBe(33);expect(s.locale).toBe('sv-SE');});
 it('includes 100 in the final demographic band without including missing',()=>{const s=readState('?view=dominant&band=50');expect(filtered(rows,s).map(d=>d.district_id)).toEqual(['b']);});
});

it('excludes pending districts from aggregate turnout and vote weights',()=>{
 const rows=[{eligible_voters:100,ballots_cast:80,valid_votes:75,foreign_background_pct:20},{eligible_voters:900,ballots_cast:null,valid_votes:null,foreign_background_pct:90}] as unknown as District[];
 expect(turnout(rows)).toBe(80);
 expect(weightedMean(rows,'foreign_background_pct','votes')).toBe(20);
});
