import type {District} from '../types';
import {number,percent} from './format';
export const socioMetrics=[
 {id:'income',label:'Renta neta media',unit:'SEK',factor:1,color:'#248675',years:[2011,2024],universe:'20+ · población de año completo · precios de 2024'},
 {id:'education',label:'Educación superior',unit:'%',factor:100,color:'#8056b4',years:[2015,2025],universe:'25–64 años hasta 2022; 25–65 desde 2023'},
 {id:'employment',label:'Empleo',unit:'%',factor:100,color:'#287caf',years:[2020,2024],universe:'20–64 años · ocupados / población · BAS'},
 {id:'unemployment',label:'Desempleo',unit:'%',factor:100,color:'#c77726',years:[2020,2024],universe:'20–64 años · desempleados / población activa · BAS'},
 {id:'young',label:'Menores de 20 años',unit:'%',factor:100,color:'#c75280',years:[2010,2025],universe:'0–19 años / todos los residentes'},
 {id:'senior',label:'65 años o más',unit:'%',factor:100,color:'#75882c',years:[2010,2025],universe:'65+ / todos los residentes'},
 {id:'population',label:'Población total',unit:'personas',factor:1,color:'#587994',years:[2010,2025],universe:'Residentes a 31 de diciembre'},
];
export const socioMapMetrics:[string,string][]=socioMetrics.filter(m=>!['income','population'].includes(m.id)).map(m=>[`socio_${m.id}_pct`,m.label+' ≈']);
export const socioMetric=(key:string)=>socioMetrics.find(m=>key===`socio_${m.id}_pct`);
export const socioYear=(d:District|undefined,key:string)=>d?.[key.replace(/_pct$/,'_year')]??'—';
export type SocioPoint={year:number;n:number|null;d:number|null;method?:string;geometry?:number;scope?:string;comparable?:boolean};
export function socioValue(p:SocioPoint,factor:number){return typeof p.n==='number'&&Number.isFinite(p.n)&&typeof p.d==='number'&&p.d>0?factor*p.n/p.d:null;}
export function aggregateSocio(cells:(SocioPoint|undefined)[],year:number,count=false):SocioPoint{
 if(!cells.length||cells.some(p=>!p||p.n===null||p.d===null||p.d<=0))return {year,n:null,d:null};
 return {year,n:cells.reduce((v,p)=>v+p!.n!,0),d:count?1:cells.reduce((v,p)=>v+p!.d!,0)};
}
export const socioAmount=(v:number|null,unit:string)=>v===null?'Sin dato':unit==='%'?percent(v):`${number(v)} ${unit==='SEK'?'SEK/año':'personas'}`;
