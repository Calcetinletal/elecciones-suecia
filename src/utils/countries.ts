export interface BirthCountry {code:string;name_sv:string;kind:string;name_es?:string;members?:string[];description?:string;source_code?:string}
export interface BirthRegion {code:string;name:string;level:string;population:number;counts:Record<string,number|null>;group_details?:Record<string,{published_country_count:number;missing_country_count:number;missing_country_codes:string[];member_count:number;status:string}>}
export interface BirthData {year:number;reference_date:string;source_url:string;downloaded_at:string;countries:BirthCountry[];regions:BirthRegion[];birth_groups?:BirthCountry[];religion?:{status:string;source_url:string;explanation:string}}
export function countryShare(region:BirthRegion,country:BirthCountry):number|null{
 const n=region.counts[country.code];
 if(typeof n!=='number'||!Number.isFinite(n)||region.population<=0)return null;
 if(n===0&&country.kind==='country'&&country.code!=='SE')return null;
 return 100*n/region.population;
}
export function countryLabel(country:BirthCountry){
 if(country.kind==='region'||country.kind==='parent')return country.name_es??country.name_sv;
 const special:Record<string,string>={'ÖOF':'País desconocido',OVFOD:'Otros países (agrupados)',SU:'Unión Soviética (antigua)',YU:'Yugoslavia (antigua)',CS:'Serbia y Montenegro (antiguo)'};
 if(special[country.code])return special[country.code];
 try {return new Intl.DisplayNames(['es'],{type:'region',fallback:'none'}).of(country.code)??country.name_sv;}catch{return country.name_sv;}
}

export function birthLabel(c:BirthCountry){return c.kind==='parent'?countryLabel(c):c.kind==='region'?`Nacimiento: ${countryLabel(c)}`:`Nacidos en ${countryLabel(c)}`;}
