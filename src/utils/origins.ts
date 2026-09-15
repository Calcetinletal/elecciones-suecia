import {countryShare,countryLabel,type BirthCountry,type BirthRegion} from './countries';
export const continentCodes=['REG_EUROPE_EX_SE','REG_AFRICA','REG_ASIA','REG_AMERICAS','REG_OCEANIA'];
export const originCandidates=(items:BirthCountry[],regions:boolean)=>items.filter(c=>regions?continentCodes.includes(c.code):c.kind==='country'&&c.code!=='SE');
export function leadingOrigin(r:BirthRegion,items:BirthCountry[],regions=false){
 const ranked=originCandidates(items,regions).filter(c=>countryShare(r,c)!==null&&(r.counts[c.code]??0)>0).sort((a,b)=>r.counts[b.code]!-r.counts[a.code]!);
 if(!ranked.length)return {code:'missing',category:null,pct:null,ranked};
 const first=ranked[0],n=r.counts[first.code]!;
 if(ranked[1]&&n===r.counts[ranked[1].code])return {code:'tie',category:null,pct:null,ranked};
 // Pooled/unknown cells can contain a country larger than the apparent winner.
 if(!regions&&(r.counts.OVFOD??0)+(r.counts['ÖOF']??0)>=n)return {code:'uncertain',category:null,pct:null,ranked};
 return {code:first.code,category:first,pct:countryShare(r,first),ranked};
}
export function originColor(code:string){
 const fixed:Record<string,string>={PARENT_FOREIGN_BORN:'#6f55bf',PARENT_BOTH_FOREIGN:'#da8031',PARENT_MIXED:'#219b8e',PARENT_BOTH_SWEDEN:'#487bbd',REG_UNASSIGNED:'#738491',REG_NON_EUROPE:'#b64c4c',missing:'#7b8793',tie:'#b1aabb',uncertain:'#a2a9b2',REG_EUROPE_EX_SE:'#8661c5',REG_AFRICA:'#d86b59',REG_ASIA:'#e6a136',REG_AMERICAS:'#36a899',REG_OCEANIA:'#3b91c6',SY:'#dc7c39',IQ:'#7469c6',FI:'#4c9cb6',PL:'#39a092',IR:'#bf6388',IN:'#bb922c',DE:'#608bc2',DK:'#b96255',NO:'#70a669',BA:'#9271b0',YU:'#b48c55',AF:'#ad6c94'};
 if(fixed[code])return fixed[code];let hash=0;for(const c of code)hash=(hash*31+c.charCodeAt(0))>>>0;return `hsl(${hash*137.508%360} 45% 48%)`;
}
export function originTitle(result:ReturnType<typeof leadingOrigin>){return result.category?countryLabel(result.category):result.code==='tie'?'Empate':result.code==='uncertain'?'Sin predominio determinable':'Sin dato';}
