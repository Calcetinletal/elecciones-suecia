import {socioMetric,socioYear} from './socio';
import type {District} from '../types';
import {finite} from './data';
import {number,percent} from './format';
export const isIncomeMetric=(key:string)=>key==='mean_net_income';
export const incomeLabel='Renta neta media anual ≈';
export const incomeDefinition='Ingreso neto personal después de impuestos, incluidos capital y transferencias. Media anual de personas de 20 años o más incluidas en la población de año completo de SCB. SEK a precios de 2024. No es salario, renta bruta, renta del hogar ni mediana.';
export const incomeEstimateNote='Estimación DeSO → distrito: se transfieren el número de personas y la suma aproximada de sus ingresos, y después se divide. Si falta un área contribuyente, no se calcula. La renta es de 2024 en el mapa 2026 y de 2022 en el mapa 2022; ambas en precios de 2024.';
export const incomeAmount=(value:unknown)=>finite(value)?`${number(value)} SEK/año`:'Sin dato';
export const metricAmount=(value:unknown,key:string)=>isIncomeMetric(key)?incomeAmount(value):percent(value);
export const metricYear=(d:District|undefined,key:string)=>socioMetric(key)?socioYear(d,key):isIncomeMetric(key)?d?.income_year??'—':d?.demography_year??'—';
export function aggregateIncome(rows:District[]){
 const known=rows.filter(d=>finite(d.mean_net_income)&&finite(d.income_population)&&d.income_population>0&&finite(d.income_total_sek));
 const people=known.reduce((n,d)=>n+(d.income_population as number),0);
 return {mean:people?known.reduce((n,d)=>n+(d.income_total_sek as number),0)/people:null,people:people||null,districts:known.length};
}
