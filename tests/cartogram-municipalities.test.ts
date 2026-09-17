import {describe,it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import parties from '../config/parties.json';
import type {District} from '../src/types';
import {cartogramMunicipalities} from '../src/utils/cartogram-municipalities';
describe('municipal cartogram totals',()=>{
 it('uses vote-count sums, not averages of district percentages',()=>{
  const fixture=(id:string,total:number,s:number)=>({district_id:id,municipality_code:'0180',municipality_name:'Stockholm',election_year:2026,valid_votes:total,eligible_voters:total*2,ballots_cast:total,...Object.fromEntries(parties.map(p=>['vote_'+p.id,p.id==='S'?s:p.id==='M'?total-s:0]))}) as unknown as District;
  const rows=[fixture('a',100,90),fixture('b',900,90)],result=cartogramMunicipalities(rows,'S+V')[0];
  expect(result.valid_votes).toBe(1000);expect(result.pct_S).toBe(18);expect(result['pct_S+V']).toBe(18);expect(result.winning_party).toBe('M');expect(result.turnout_pct).toBe(50);
  expect(cartogramMunicipalities([{...rows[0],vote_S:null},rows[1]],'S')[0].vote_S).toBeNull();
 });
 it('preserves every published party total in both election editions',()=>{
  const manifest=JSON.parse(readFileSync('public/data/manifest.json','utf8'));
  for(const year of [2022,2026]){const entry=manifest.years.find((y:{year:number})=>y.year===year),rows:District[]=JSON.parse(gunzipSync(readFileSync('public/data/'+entry.table)).toString()),municipalities=cartogramMunicipalities(rows,'S');
   expect(municipalities).toHaveLength(290);
   const geometry=JSON.parse(gunzipSync(readFileSync(`public/data/${year}/municipalities.geojson.gz`)).toString());
   expect(geometry.provenance.year).toBe(year);expect(geometry.provenance.source_sha256).toBe(createHash('sha256').update(readFileSync('public/data/'+entry.geometry)).digest('hex'));expect(geometry.features.map((f:{properties:{municipality_code:string}})=>f.properties.municipality_code).sort()).toEqual(municipalities.map(d=>d.municipality_code).sort());
   for(const field of ['valid_votes',...parties.map(p=>'vote_'+p.id)])expect(municipalities.reduce((n,d)=>n+(d[field] as number),0)).toBe(rows.filter(d=>d.election_reported!==false&&d.valid_votes!>0).reduce((n,d)=>n+(d[field] as number),0));
  }
 });
});
