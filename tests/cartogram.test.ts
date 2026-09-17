import {describe,it,expect} from 'vitest';
import {makeCartogramNodes,layoutCartogram,maximumOverlap,voteSlices} from '../src/utils/cartogram';
import {readState,routeUrl} from '../src/utils/state';
import type {District} from '../src/types';
describe('vote-area cartogram',()=>{
 it('encodes counts in area, never in radius, and excludes absent/zero weights',()=>{
  const nodes=makeCartogramNodes([{id:'a',x:0,y:0,votes:100},{id:'b',x:0,y:0,votes:400},{id:'z',x:0,y:0,votes:0},{id:'n',x:0,y:0,votes:NaN}]);
  expect(nodes).toHaveLength(2);expect(nodes[1].r/nodes[0].r).toBeCloseTo(2);expect(nodes.reduce((n,p)=>n+Math.PI*p.r*p.r,0)).toBeCloseTo(180000);
 });
 it('separates coincident circles deterministically without changing sizes or votes',()=>{
  const nodes=makeCartogramNodes(Array.from({length:100},(_,i)=>({id:String(i),x:i%3,y:i%4,votes:100+i*13})));
  const placed=layoutCartogram(nodes);expect(maximumOverlap(placed)).toBeLessThan(.001);expect(placed.map(n=>[n.id,n.votes,n.r])).toEqual(nodes.map(n=>[n.id,n.votes,n.r]));expect(layoutCartogram(nodes)).toEqual(placed);
 });
 it('preserves the published denominator and makes missing party counts explicit',()=>{
  const d={valid_votes:100,vote_S:25,vote_V:10} as unknown as District;
  const slices=voteSlices(d);expect(slices.find(p=>p.id==='S')!.share).toBe(.25);expect(slices.find(p=>p.id==='missing')!.share).toBe(.65);expect(slices.reduce((n,p)=>n+p.share,0)).toBe(1);
  expect(voteSlices({...d,valid_votes:20})).toEqual([{id:'missing',color:'#7b8793',votes:20,share:1}]);
  expect(voteSlices({...d,election_reported:false})).toEqual([]);
 });
 it('shares the representation and preserves party combinations',()=>{
  const s=readState('?view=cartogram&cartogramMode=shares&party=S%2BV&metric=party');expect(s.view).toBe('cartogram');expect(s.cartogramMode).toBe('shares');expect(s.party).toBe('S+V');expect(readState(new URL(routeUrl('',s),'https://example.test').search)).toEqual(s);
 });
});
