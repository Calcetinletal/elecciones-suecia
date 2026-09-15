import {describe,it,expect} from 'vitest';
import {readState} from '../src/utils/state';
import {selectElection,electionSelection,comparisonElectionKey,comparisonElectionLabel} from '../src/utils/election-view';
describe('independent comparison selectors',()=>{
 it('selects either categorical election view without changing population origin or remembered party',()=>{
  const s=readState('?view=compare&metric=born_europe_ex_sweden_pct&party=S');
  for(const option of ['winning_party','winning_block']){
   selectElection(s,option);expect(s.view).toBe('compare');expect(s.metric).toBe('born_europe_ex_sweden_pct');expect(s.party).toBe('S');expect(electionSelection(s)).toBe(option);expect(comparisonElectionKey(s)).toBe(option);
  }
  expect(comparisonElectionLabel(s)).toBe('Bloque dominante');
 });
 it('returns to individual vote percentages and round-trips both selectors in a URL',()=>{
  const s=readState('?view=compare&metric=foreign_born_pct&electionMetric=winning_block&party=SD');
  expect(electionSelection(s)).toBe('winning_block');selectElection(s,'M');
  expect(s.electionMetric).toBe('party');expect(comparisonElectionKey(s)).toBe('pct_M');expect(s.metric).toBe('foreign_born_pct');
  const loaded=readState('?'+new URLSearchParams(Object.entries(s).map(([k,v])=>[k,String(v)])));
  expect(loaded).toEqual(s);
 });
 it('keeps old compare URLs on their individual party and sanitizes unknown modes',()=>{
  expect(comparisonElectionKey(readState('?view=compare&party=S'))).toBe('pct_S');
  expect(readState('?view=compare&electionMetric=invalid').electionMetric).toBe('party');
 });
 it('preserves standalone electoral selection behavior',()=>{
  const s=readState('?view=electoral&party=SD');selectElection(s,'winning_block');expect(s.metric).toBe('winning_block');expect(s.party).toBe('SD');selectElection(s,'S');expect(s.metric).toBe('party');expect(s.party).toBe('S');
 });
});
