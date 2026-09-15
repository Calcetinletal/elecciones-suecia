import {describe,it,expect} from 'vitest';
import {decorateDistrict,blockWinner,districtOrigin} from '../src/utils/categories';
import {leadingOrigin,originCandidates} from '../src/utils/origins';
import {districtHover} from '../src/components/hover';
import {readState} from '../src/utils/state';
import type {District} from '../src/types';
import type {BirthCountry,BirthRegion} from '../src/utils/countries';
const d={election_year:2026,election_reported:true,valid_votes:1000,vote_S:210,vote_V:70,vote_MP:40,vote_C:80,vote_M:200,vote_SD:230,vote_KD:70,vote_L:50,born_sweden_count:800,born_europe_ex_sweden_count:60,born_rest_world_unknown_count:140} as unknown as District;
describe('categorical district maps',()=>{
 it('sums votes and keeps all valid votes as denominator',()=>{const result=blockWinner(d);expect(result.code).toBe('right_block');expect(result.pct).toBe(55);});
 it('preserves ties and pending or incomplete counts',()=>{expect(blockWinner({...d,vote_SD:80}).code).toBe('tie');expect(blockWinner({...d,election_reported:false}).code).toBe('missing');expect(blockWinner({...d,vote_L:null}).code).toBe('missing');});
 it('excludes Sweden from foreign origin, retains unknown and missing data',()=>{expect(districtOrigin(d)).toEqual({code:'rest',pct:70});expect(districtOrigin({...d,born_rest_world_unknown_count:60}).code).toBe('tie');expect(districtOrigin({...d,born_rest_world_unknown_count:null}).code).toBe('missing');});
 it('keeps category state in URLs and CSV rows',()=>{expect(readState('?view=electoral&metric=winning_block').metric).toBe('winning_block');expect(readState('?view=compare&metric=common_origin').metric).toBe('common_origin');expect(decorateDistrict(d).winning_block).toBe('right_block');});
 it('escapes names and makes pending results explicit in the compact hover',()=>{const html=districtHover({...d,district_name:'<img onerror=x>',district_id:'x',election_reported:false},'winning_party');expect(html).toContain('&lt;img onerror=x&gt;');expect(html).toContain('Recuento pendiente');expect(districtHover(d,'common_origin')).toContain('desconocido');expect(html).not.toContain('hover-runners');});
});
const countries:BirthCountry[]=[{code:'SE',kind:'country',name_sv:'Sweden'},{code:'SY',kind:'country',name_sv:'Syria'},{code:'FI',kind:'country',name_sv:'Finland'},{code:'OVFOD',kind:'group',name_sv:'Other'}];
const region:BirthRegion={code:'1',name:'Test',level:'municipality',population:1000,counts:{SE:800,SY:100,FI:50,OVFOD:10}};
describe('most common published foreign birthplace',()=>{
 it('uses individual foreign countries, not Sweden or pooled categories',()=>{expect(leadingOrigin(region,countries).code).toBe('SY');expect(leadingOrigin(region,countries).pct).toBe(10);});
 it('shows ties, missing and ambiguous pooled cells separately',()=>{expect(leadingOrigin({...region,counts:{SY:50,FI:50}},countries).code).toBe('tie');expect(leadingOrigin({...region,counts:{SY:null,FI:0}},countries).code).toBe('missing');expect(leadingOrigin({...region,counts:{SY:20,FI:10,OVFOD:21}},countries).code).toBe('uncertain');});
 it('compares only disjoint continental subtotals excluding Sweden',()=>{const items=['REG_AFRICA','REG_ASIA','REG_EUROPE_EX_SE','REG_EUROPE','REG_NON_EUROPE','REG_AMERICAS','REG_LATIN_AMERICA','REG_OCEANIA'].map(code=>({code,kind:'region',name_sv:code}));expect(originCandidates(items,true).map(c=>c.code)).toEqual(['REG_AFRICA','REG_ASIA','REG_EUROPE_EX_SE','REG_AMERICAS','REG_OCEANIA']);});
});
