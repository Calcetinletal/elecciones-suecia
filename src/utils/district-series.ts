import type {District} from '../types';
import parties from '../../config/parties.json';
export type DistrictObservation={year:number;total?:number|null;population?:number|null;counts:Record<string,number|null>;pct?:Record<string,number|null>;status?:string;ckm?:boolean;unavailable_reason?:string};
export const districtBirthSeries=[
 {code:'born_sweden',name:'Suecia',color:'#487bbd',emblem:'SE'},
 {code:'born_europe_ex_sweden',name:'Europa excepto Suecia',color:'#8661c5',emblem:'REG_EUROPE_EX_SE'},
 {code:'born_rest_world_unknown',name:'Resto del mundo + desconocido',color:'#d86b59',emblem:'WORLD'}
];
const finite=(n:unknown):n is number=>typeof n==='number'&&Number.isFinite(n);
function total(rows:District[],key:string){const cells=rows.map(r=>r[key]);return rows.length&&cells.every(finite)?(cells as number[]).reduce((a,b)=>a+b,0):null;}
export function voteObservation(rows:District[]):DistrictObservation{
 const denominator=total(rows,'valid_votes');const counts=Object.fromEntries(parties.map(p=>[p.id,total(rows,'vote_'+p.id)]));
 return {year:Number(rows[0].election_year),total:denominator,counts,pct:Object.fromEntries(Object.entries(counts).map(([k,n])=>[k,n!==null&&denominator?100*n/denominator:null])),status:String(rows[0].election_status??'definitive')};
}
export function birthObservation(rows:District[]):DistrictObservation{
 const year=Number(rows[0].birth_regions_year??rows[0].demography_year);
 return {year,population:total(rows,'birth_regions_population'),counts:Object.fromEntries(districtBirthSeries.map(s=>[s.code,total(rows,s.code+'_count')])),ckm:year===2025,unavailable_reason:rows.some(r=>r.birth_regions_method==='historical_grid_unavailable')?'Sin estimación: falta una cuadrícula histórica incorporada para repartir áreas DeSO parciales':rows.some(r=>r.birth_regions_method==='insufficient_spatial_coverage')?'Estimación excluida: cobertura geográfica insuficiente':rows.some(r=>r.birth_regions_complete===false)?'Estimación no disponible: faltan celdas de origen':undefined};
}
export function priorIds(d:District){return ['comparable','comparable_aggregate'].includes(String(d.comparison_status))?String(d.comparison_old_ids??'').split(';').filter(Boolean):[];}
/** Published correspondence only. Never treat a 2022 member of a later merger as its whole. */
export function comparableDistrictRows(selected:District,otherEdition:District[]){
 const year=Number(selected.election_year);
 if(year===2026){
  const ids=priorIds(selected);const byId=new Map(otherEdition.map(r=>[r.district_id,r]));
  if(!ids.length||new Set(ids).size!==ids.length||ids.some(id=>!byId.has(id)))return null;
  const old=ids.map(id=>byId.get(id)!);
  if(old.some(r=>r.election_year!==2022||r.municipality_code!==selected.municipality_code))return null;
  return {old,current:[selected],aggregate:ids.length>1};
 }
 if(year===2022){
  const candidates=otherEdition.filter(r=>r.election_year===2026&&priorIds(r).includes(selected.district_id));
  if(candidates.length!==1||priorIds(candidates[0]).length!==1||candidates[0].municipality_code!==selected.municipality_code)return null;
  return {old:[selected],current:[candidates[0]],aggregate:false};
 }
 return null;
}

export type EarlierDistrictEdition={rows:District[];previous:Record<string,string[]>;source:string};
/** Extend only a complete set of official links. Never duplicate a predecessor in a sum. */
export function earlierDistrictRows(rows:District[],edition:EarlierDistrictEdition){
 const ids=rows.flatMap(r=>edition.previous[r.district_id]??[]);
 if(rows.some(r=>!edition.previous[r.district_id]?.length)||!ids.length||new Set(ids).size!==ids.length)return null;
 const byId=new Map(edition.rows.map(r=>[r.district_id,r]));
 if(ids.some(id=>!byId.has(id)))return null;
 const old=ids.map(id=>byId.get(id)!);
 return old.every(r=>r.election_year===2018&&r.municipality_code===rows[0].municipality_code)?old:null;
}

/** Reference editions only: same published code, name and municipality are not a comparable link. */
export function sameNamedDistrict(selected:District,rows:District[]){
 const matches=rows.filter(r=>r.district_id===selected.district_id&&r.municipality_code===selected.municipality_code&&r.district_name===selected.district_name);
 return matches.length===1?matches[0]:null;
}

export type DistrictArchive={editions:Record<string,District[]>;links:Record<string,Record<string,string[]>>;birth:Record<string,Record<string,DistrictObservation[]>>};
export type HistorySegment={rows:District[];year:number;breakBefore:boolean};
/** Exact published links join lines. Reused codes retain reference observations with a break. */
export function archiveDistrictChain(selected:District,archive:DistrictArchive):HistorySegment[]{
 const years=Object.keys(archive.editions).map(Number).sort((a,b)=>a-b);
 const start=years.indexOf(Number(selected.election_year));if(start<0)return [{rows:[selected],year:Number(selected.election_year),breakBefore:false}];
 const chain:HistorySegment[]=[{rows:[selected],year:years[start],breakBefore:false}];
 for(let i=start;i>0;i--){
  const current=chain[0],older=archive.editions[String(years[i-1])];
  const byId=new Map(older.map(r=>[r.district_id,r]));
  const links=current.rows.map(r=>archive.links[String(current.year)]?.[r.district_id]);
  const ids=links.flatMap(ids=>ids??[]);
  const comparable=links.every(ids=>ids?.length)&&new Set(ids).size===ids.length&&ids.every(id=>byId.has(id));
  const previous=comparable?ids.map(id=>byId.get(id)!):current.rows.map(r=>byId.get(r.district_id));
  if(previous.some(r=>!r)||!previous.length)break;
  current.breakBefore=!comparable;
  chain.unshift({rows:previous as District[],year:years[i-1],breakBefore:false});
 }
 for(let i=start+1;i<years.length;i++){
  const current=chain.at(-1)!,newer=archive.editions[String(years[i])],ids=current.rows.map(r=>r.district_id);
  const candidates=newer.filter(r=>{const old=archive.links[String(years[i])]?.[r.district_id];return old?.length===ids.length&&old.every(id=>ids.includes(id));});
  let next:District|undefined;let comparable=false;
  if(candidates.length===1){next=candidates[0];comparable=true;}
  else if(current.rows.length===1)next=newer.find(r=>r.district_id===ids[0]);
  if(!next)break;
  chain.push({rows:[next],year:years[i],breakBefore:!comparable});
 }
 return chain;
}
export function archiveBirthRows(segment:HistorySegment,archive:DistrictArchive):DistrictObservation[]{
 const histories=segment.rows.map(r=>archive.birth[String(segment.year)]?.[r.district_id]??[]);
 const years=[...new Set(histories.flatMap(rows=>rows.map(r=>r.year)))].sort((a,b)=>a-b);
 return years.map(year=>{
  const cells=histories.map(rows=>rows.find(r=>r.year===year));
  const sum=(get:(r:DistrictObservation)=>unknown)=>cells.every(r=>r&&finite(get(r)))?cells.reduce((n,r)=>n+(get(r!) as number),0):null;
  return {year,population:sum(r=>r.population),counts:Object.fromEntries(districtBirthSeries.map(s=>[s.code,sum(r=>r.counts[s.code])])),ckm:year===2025,unavailable_reason:cells.find(r=>r?.unavailable_reason)?.unavailable_reason??(cells.some(r=>!r)?'Sin observación para este ámbito histórico':undefined)};
 });
}
