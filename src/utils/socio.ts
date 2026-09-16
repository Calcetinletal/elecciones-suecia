import type {District} from '../types';
import {number,percent} from './format';
export const socioMetrics=[
 {id:'income',description:'Ingreso neto anual medio por persona: ingresos del trabajo y del capital más transferencias, después de impuestos. Incluye a las personas de 20 años o más de la población de año completo de SCB. Importes ajustados a precios de 2024; no es el salario ni la mediana.',label:'Renta neta media',unit:'SEK',factor:1,color:'#248675',years:[2011,2024],universe:'20+ · población de año completo · precios de 2024'},
 {id:'education',description:'Porcentaje con estudios posteriores a la secundaria, tanto de menos de tres años como de tres años o más. El denominador incluye a todas las personas del grupo de edad, también aquellas sin nivel educativo conocido. Edad: 25–64 hasta 2022; 25–65 desde 2023.',label:'Educación superior',unit:'%',factor:100,color:'#8056b4',years:[2015,2025],universe:'25–64 años hasta 2022; 25–65 desde 2023'},
 {id:'employment',description:'Personas ocupadas como porcentaje de todos los residentes de 20–64 años, según BAS de SCB. El denominador incluye también a desempleados y personas fuera de la población activa.',label:'Empleo',unit:'%',factor:100,color:'#287caf',years:[2020,2024],universe:'20–64 años · ocupados / población · BAS'},
 {id:'unemployment',description:'Personas desempleadas como porcentaje de la población activa de 20–64 años (ocupados más desempleados), según BAS de SCB. El denominador no es toda la población.',label:'Desempleo',unit:'%',factor:100,color:'#c77726',years:[2020,2024],universe:'20–64 años · desempleados / población activa · BAS'},
 {id:'young',description:'Residentes de 0–19 años divididos por todos los residentes, multiplicado por 100. Población a 31 de diciembre de cada año.',label:'Menores de 20 años',unit:'%',factor:100,color:'#c75280',years:[2010,2025],universe:'0–19 años / todos los residentes'},
 {id:'senior',description:'Residentes de 65 años o más divididos por todos los residentes, multiplicado por 100. Población a 31 de diciembre de cada año.',label:'65 años o más',unit:'%',factor:100,color:'#75882c',years:[2010,2025],universe:'65+ / todos los residentes'},
 {id:'population',description:'Número total de residentes registrados a 31 de diciembre de cada año, de todas las edades. Es un recuento de personas, no un porcentaje.',label:'Población total',unit:'personas',factor:1,color:'#587994',years:[2010,2025],universe:'Residentes a 31 de diciembre'},
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
