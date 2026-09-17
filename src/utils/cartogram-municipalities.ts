import type {District} from '../types';
import parties from '../../config/parties.json';
import {decorateDistrict} from './categories';
import {hasVotes} from './cartogram';
import {preparePartySum} from './party-selection';

/** Municipal totals are sums of the displayed geographic districts, never means of percentages. */
export function cartogramMunicipalities(rows:District[],selection:string):District[]{
 const groups=new Map<string,District[]>();for(const d of rows){const group=groups.get(d.municipality_code)??[];group.push(d);groups.set(d.municipality_code,group);}
 const result=[...groups].map(([id,group])=>{
  const valid=group.filter(hasVotes),first=group[0];
  const sum=(key:string)=>valid.length&&valid.every(d=>typeof d[key]==='number'&&Number.isFinite(d[key]))?valid.reduce((n,d)=>n+(d[key] as number),0):null;
  const total=sum('valid_votes'),eligible=sum('eligible_voters'),ballots=sum('ballots_cast');
  const d={district_id:id,district_name:first.municipality_name,municipality_code:id,municipality_name:first.municipality_name,county_code:first.county_code,county_name:first.county_name,election_year:first.election_year,election_reported:valid.length>0,valid_votes:total,eligible_voters:eligible,ballots_cast:ballots,turnout_pct:eligible&&ballots!==null?100*ballots/eligible:null,district_count:group.length} as unknown as District;
  for(const p of parties){const votes=sum('vote_'+p.id);d['vote_'+p.id]=votes;d['pct_'+p.id]=total&&votes!==null?100*votes/total:null;}
  const ranked=parties.map(p=>({id:p.id,v:d['vote_'+p.id]})).filter((p):p is {id:string;v:number}=>typeof p.v==='number').sort((a,b)=>b.v-a.v);
  d.winning_party=ranked.length===parties.length&&total?ranked[0].id:null;d.winning_party_pct=d.winning_party?100*ranked[0].v/total!:null;d.winning_party_tie=!!d.winning_party&&ranked[0].v===ranked[1].v;
  return decorateDistrict(d);
 });preparePartySum(result,selection);return result;
}
