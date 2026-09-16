import {describe,it,expect} from 'vitest';
import type {District} from '../src/types';
import {combinedVote,normalizeParties,preparePartySum} from '../src/utils/party-selection';
import {readState,routeUrl} from '../src/utils/state';
import {selectElection,comparisonElectionKey} from '../src/utils/election-view';
import {value} from '../src/utils/data';
import {districtHover} from '../src/components/hover';

describe('custom party sums',()=>{
 it('uses counts, not rounded shares, with all valid votes as denominator',()=>{
  const d={valid_votes:3,vote_S:1,vote_V:1,pct_S:33.3,pct_V:33.3} as unknown as District;
  expect(combinedVote(d,'S+V').pct).toBe(200/3);
  preparePartySum([d],'S+V');
  expect(value(d,readState('?metric=party&party=S%2BV'))).toBe(200/3);
  expect(d.vote_S).toBe(1);expect(d['vote_S+V']).toBe(2);
 });
 it('keeps missing, pending and zero denominators missing; a counted zero is valid',()=>{
  const d={valid_votes:100,vote_S:0,vote_V:0} as unknown as District;
  expect(combinedVote(d,'S+V').pct).toBe(0);
  for(const extra of [{vote_V:null},{valid_votes:0},{election_reported:false},{vote_S:-1}])expect(combinedVote({...d,...extra} as District,'S+V').pct).toBeNull();
 });
 it('deduplicates valid parties and preserves the selection and origin in shared links',()=>{
  expect(normalizeParties('V+S+S+invalid')).toBe('S+V');
  const s=readState('?view=compare&metric=born_rest_world_unknown_pct&party=S');
  selectElection(s,'V+S');expect(comparisonElectionKey(s)).toBe('pct_S+V');expect(s.metric).toBe('born_rest_world_unknown_pct');
  const loaded=readState(new URL(routeUrl('',s),'https://example.test').search);expect(loaded).toEqual(s);
  selectElection(s,'winning_block');expect(s.party).toBe('S+V');
  selectElection(s,'MP');expect(s.party).toBe('MP');
 });
 it('shows the mapped combined share in the hover',()=>{
  const d={valid_votes:100,vote_S:30,vote_V:12,district_name:'Example'} as unknown as District;
  preparePartySum([d],'S+V');expect(districtHover(d,'pct_S+V')).toContain('S + V');expect(districtHover(d,'pct_S+V')).toContain('42 %');
 });
});
