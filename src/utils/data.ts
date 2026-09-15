import type {District,State} from '../types';
export const finite=(x:unknown):x is number=>typeof x==='number'&&Number.isFinite(x);
export function filtered(rows:District[],s:State){return rows.filter(d=>(!s.county||d.county_code===s.county)&&(!s.municipality||d.municipality_code===s.municipality||d.municipality_name===s.municipality)&&(s.quality!=='high'||d.coverage_quality==='high_coverage')&&(s.view!=='dominant'||s.band==='all'||(finite(d.foreign_background_pct)&&d.foreign_background_pct>=Number(s.band)&&(s.band==='50'||d.foreign_background_pct<Number(s.band)+10))));}
export function value(d:District,s:State):number|null{const key=s.view==='dominant'?'winning_party_pct':s.view==='demography'||s.view==='compare'?s.metric:s.view==='bivariate'?'foreign_background_pct':s.metric==='party'?`pct_${s.party}`:s.metric==='winning_party'?'winning_party_pct':s.metric==='winning_block'?'winning_block_pct':s.metric;if(key==='common_origin')return finite(d.common_origin_pct)?d.common_origin_pct:null;return finite(d[key])?d[key] as number:null;}
export function weightedMean(rows:District[],key:string,weight='equal'):number|null{
 let n=0,w=0;for(const d of rows){if(finite(d[key])){const wi=weight==='votes'?d.valid_votes:1;if(!finite(wi)||wi<=0)continue;n+=(d[key] as number)*wi;w+=wi;}}return w?n/w:null;
}
export function sum(rows:District[],key:string):number|null{const a=rows.map(d=>d[key]).filter(finite);return a.length?a.reduce((s,x)=>s+x,0):null;}
export function turnout(rows:District[]):number|null{const reported=rows.filter(d=>finite(d.ballots_cast)&&finite(d.eligible_voters));const eligible=sum(reported,'eligible_voters');return eligible?100*(sum(reported,'ballots_cast')??0)/eligible:null;}
