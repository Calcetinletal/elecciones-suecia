import parties from '../../config/parties.json';
import type {District} from '../types';

const valid=(n:unknown):n is number=>typeof n==='number'&&Number.isFinite(n)&&n>=0;
export function partyIds(selection:string){
 const wanted=new Set(selection.split(/[+ ,]+/));
 return parties.filter(p=>wanted.has(p.id)).map(p=>p.id);
}
export function normalizeParties(selection:string){return partyIds(selection).join('+')||'SD';}
export function partyLabel(selection:string){return partyIds(selection).map(id=>id==='other'?'Otros':id).join(' + ');}
export function combinedVote(d:District,selection:string){
 const ids=partyIds(selection),counts=ids.map(id=>d['vote_'+id]);
 if(!ids.length||d.election_reported===false||!valid(d.valid_votes)||d.valid_votes===0||!counts.every(valid))return {votes:null,pct:null};
 const votes=(counts as number[]).reduce((a,b)=>a+b,0);
 return {votes,pct:100*votes/d.valid_votes};
}
/** Derived fields let maps, rankings, analysis and CSV use the same exact sum. */
export function preparePartySum(rows:District[],selection:string){
 if(partyIds(selection).length<2)return;
 for(const d of rows){const v=combinedVote(d,selection);d['vote_'+selection]=v.votes;d['pct_'+selection]=v.pct;}
}
