import {escapeHtml as e} from './format';
import blocks from '../../config/blocks.json';
import parties from '../../config/parties.json';
import type {District} from '../types';
const valid=(n:unknown):n is number=>typeof n==='number'&&Number.isFinite(n);
export const blockDefinitions=[{id:'left_block',name:'S · V · MP · C',color:'#cf4b76'},{id:'right_block',name:'M · SD · KD · L',color:'#4275d4'}];
export const originDefinitions=[{id:'europe',name:'Europa excepto Suecia',color:'#8661c5'},{id:'rest',name:'Resto del mundo + desconocido',color:'#e28b37'}];
export function blockWinner(d:District){
 const config=(blocks as Record<string,Record<string,string[]>>)[String(d.election_year)];
 if(!config||d.election_reported===false||!valid(d.valid_votes)||d.valid_votes<=0)return {code:'missing',pct:null,totals:[]};
 const totals=blockDefinitions.map(b=>{const ids=config[b.id]??[];const votes=ids.map(id=>d['vote_'+id]);return {...b,votes:ids.length&&votes.every(valid)?(votes as number[]).reduce((a,b)=>a+b,0):null};});
 if(totals.some(b=>b.votes===null))return {code:'missing',pct:null,totals};
 const ranked=[...totals].sort((a,b)=>b.votes!-a.votes!);const top=ranked[0];
 return {code:top.votes===ranked[1].votes?'tie':top.id,pct:100*top.votes!/d.valid_votes,totals};
}
export function districtOrigin(d:District){
 const a=d.born_europe_ex_sweden_count,b=d.born_rest_world_unknown_count;
 if(!valid(a)||!valid(b)||a<0||b<0||a+b<=0)return {code:'missing',pct:null};
 return {code:Math.abs(a-b)<.000001?'tie':a>b?'europe':'rest',pct:100*Math.max(a,b)/(a+b)};
}
export function decorateDistrict(d:District):District{
 const block=blockWinner(d),origin=districtOrigin(d);
 return {...d,winning_block:block.code,winning_block_pct:block.pct,common_origin:origin.code,common_origin_pct:origin.pct,common_origin_definition:'SCB Europe except Sweden vs rest of world including unknown; excludes Sweden; spatial estimate',block_definition:'Analytical grouping S+V+MP+C / M+SD+KD+L; other parties excluded, percentage over all valid votes'};
}
export function partyBadge(id:string){
 const p=parties.find(p=>p.id===id),color=p?.color??'#738594';
 return `<span class="party-badge" style="--party:${color}" title="${e(p?.name??id)}" aria-label="${e(p?.name??id)}">${id==='other'?'···':e(id)}</span>`;
}
export function categoryLabel(key:string,code:unknown){return code==='tie'?'Empate':code==='missing'||code===null?'Sin dato':key==='winning_block'?blockDefinitions.find(x=>x.id===code)?.name??'Sin dato':key==='common_origin'?originDefinitions.find(x=>x.id===code)?.name??'Sin dato':parties.find(x=>x.id===code)?.name??String(code);}
export const isCategorical=(key:string)=>['winning_party','winning_block','common_origin'].includes(key);
