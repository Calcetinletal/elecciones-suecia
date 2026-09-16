import {partyLabel} from '../utils/party-selection';
import {isIncomeMetric,incomeAmount} from '../utils/income';
import {comparisonElectionLabel} from '../utils/election-view';
import {blockDefinitions,originDefinitions,partyBadge} from '../utils/categories';
import {demographicLabel,isBirthRegionMetric} from '../utils/demography';
import {scaleSequential} from 'd3-scale';
import {interpolateYlGnBu,interpolateRdBu} from 'd3-scale-chromatic';
import parties from '../../config/parties.json';
import type {District,State} from '../types';
import {quantile} from '../analysis/statistics';
import {finite} from '../utils/data';
import {escapeHtml as e,percent} from '../utils/format';
export {parties};
export const bivariate=['#e8e8e8','#ace4e4','#5ac8c8','#dfb0d6','#a5add3','#5698b9','#be64ac','#8c62aa','#3b4994'];
export const divergent=scaleSequential(interpolateRdBu).domain([-30,30]);
export const sequential=scaleSequential(interpolateYlGnBu).domain([0,100]);
export function thresholds(rows:District[],key:string){const a=rows.map(d=>d[key]).filter(finite);return [quantile(a,1/3)??0,quantile(a,2/3)??0];}
/** A stable national P5–P95 scale; outliers retain their values and use end colours. */
export function percentageScale(values:number[]){
 const valid=values.filter(finite);
 if(!valid.length)return {min:0,max:100,lowClipped:false,highClipped:false};
 const lo=quantile(valid,.05)!,hi=quantile(valid,.95)!;
 const step=hi-lo<5?.1:hi-lo<20?1:5;
 let min=Math.max(0,Math.floor(lo/step)*step),max=Math.min(100,Math.ceil(hi/step)*step);
 if(max<=min){min=Math.max(0,Math.min(99,lo-.5));max=Math.min(100,min+1);}
 min=+min.toFixed(2);max=+max.toFixed(2);
 return {min,max,lowClipped:valid.some(v=>v<min),highClipped:valid.some(v=>v>max)};
}
export function incomeScale(values:number[]){
 const valid=values.filter(finite);if(!valid.length)return {min:0,max:500000,lowClipped:false,highClipped:false};
 const low=quantile(valid,.05)!,high=quantile(valid,.95)!,step=10000;
 let min=Math.floor(low/step)*step,max=Math.ceil(high/step)*step;if(max<=min)max=min+step;
 return {min,max,lowClipped:valid.some(v=>v<min),highClipped:valid.some(v=>v>max)};
}
export function metricScale(rows:District[],key:string){return (isIncomeMetric(key)?incomeScale:percentageScale)(rows.map(d=>d[key]).filter(finite));}
export function scaleStops(domain:{min:number;max:number}):[number,string][]{return Array.from({length:11},(_,i)=>[domain.min+(domain.max-domain.min)*i/10,sequential(i*10)]);}
export function scaleLabels(domain:ReturnType<typeof percentageScale>){return `<div class="scale-labels"><span>${domain.lowClipped?'≤ ':''}${percent(domain.min)}</span><span>${percent((domain.min+domain.max)/2)}</span><span>${domain.highClipped?'≥ ':''}${percent(domain.max)}</span></div>`;}
export function numericMetric(s:State){return s.metric.startsWith('delta_')?s.metric:s.view==='demography'?s.metric:s.metric==='turnout_pct'?'turnout_pct':`pct_${s.party}`;}
export function label(s:State){
 if(s.view==='compare')return demographicLabel(s.metric)+' / '+comparisonElectionLabel(s);
 if(isIncomeMetric(s.metric))return 'Renta neta media anual ≈';
 if(s.metric==='winning_block')return 'Bloque más votado';
 if(s.metric==='common_origin')return 'Región extranjera predominante ≈';
 if(s.metric.startsWith('delta_')&&s.view==='electoral')return 'Cambio 2022 → 2026 · '+s.metric.replace('delta_pct_','voto ').replace('delta_turnout_pct','participación');
 return s.view==='bivariate'?`Origen extranjero × voto ${partyLabel(s.party)}`:s.view==='dominant'||s.metric==='winning_party'?'Partido ganador':s.metric==='turnout_pct'?'Participación electoral':isBirthRegionMetric(s.metric)?demographicLabel(s.metric):s.metric==='foreign_born_pct'?'Nacidos fuera de Suecia¹':s.metric==='foreign_citizens_pct'?'Ciudadanía extranjera¹':s.view==='demography'?'Origen extranjero':'Voto '+partyLabel(s.party);
}
function legendContent(s:State,rows:District[]){
 if(s.metric==='winning_block'||s.metric==='common_origin'){const blocks=s.metric==='winning_block';return `<b>${e(label(s))}</b><div class="categorical-legend">${(blocks?blockDefinitions:originDefinitions).map(c=>`<span><i style="background:${c.color}"></i>${e(c.name)}</span>`).join('')}<span><i style="background:#b1aabb"></i>Empate</span><span><i style="background:#7b8793"></i>Sin dato</span></div><small>${blocks?'Agrupación analítica; suma de votos.':'Dos grupos SCB; excluye Suecia. Estimación por distrito. No identifica países individuales.'}${s.view==='compare'?'<br>Mapa derecho: % voto, de 0 a 100 %.':''}</small>`;}

 if(s.metric.startsWith('delta_')&&s.view==='electoral')return `<b>${e(label(s))}</b><div class="scale">${[-30,-20,-10,0,10,20,30].map(v=>`<i style="background:${divergent(v)}"></i>`).join('')}</div><div class="scale-labels"><span>−30 pp</span><span>0</span><span>+30 pp</span></div><small>Solo distritos comparables. Gris: límites cambiados, unidad nueva o sin comparación.</small>`;
 if(s.view==='bivariate'){const x=thresholds(rows,'foreign_background_pct'),y=thresholds(rows,`pct_${s.party}`);return `<b>Cuantiles nacionales · 3 × 3</b><div class="biv-legend"><span class="vertical">Voto ${e(partyLabel(s.party))} →</span><div class="biv-grid">${[...bivariate.slice(6),...bivariate.slice(3,6),...bivariate.slice(0,3)].map(c=>`<span style="background:${c}"></span>`).join('')}</div></div><span>Origen extranjero →</span><small>X: ${percent(x[0])} / ${percent(x[1])}<br>Y: ${percent(y[0])} / ${percent(y[1])}<br>Bajo ≤ primer corte; alto &gt; segundo corte.<br>Gris claro: bajo en ambos; gris oscuro: sin dato.</small>`;}
 if(s.view==='dominant'||(s.view==='electoral'&&s.metric==='winning_party'))return `<b>Partido ganador</b><div class="party-legend">${parties.map(p=>`<span>${partyBadge(p.id)}${p.id==='other'?'Otros':''}</span>`).join('')}</div><small>Gris: sin resultado · Lila: empate.</small>`;
 const domain=metricScale(rows,numericMetric(s));
 if(isIncomeMetric(s.metric))return `<b>Renta neta · ${rows[0]?.income_year??'—'} ≈</b><div class="scale" data-scale-min="${domain.min}" data-scale-max="${domain.max}">${scaleStops(domain).map(([,color])=>`<i style="background:${color}"></i>`).join('')}</div><div class="scale-labels"><span>${domain.lowClipped?'≤ ':''}${incomeAmount(domain.min)}</span><span>${domain.highClipped?'≥ ':''}${incomeAmount(domain.max)}</span></div><small>Personas de 20+ · precios de 2024. Estimación espacial de la media, no mediana ni salario. Escala nacional P5–P95; los extremos saturan el color, no recortan los datos. Gris: sin dato.</small>`;
 return `<b>${e(label(s))}</b><div class="scale" data-scale-min="${domain.min}" data-scale-max="${domain.max}">${scaleStops(domain).map(([,color])=>`<i style="background:${color}"></i>`).join('')}</div>${scaleLabels(domain)}<small>Escala nacional por indicador · percentiles 5–95 redondeados. Los valores fuera de los límites usan los colores extremos; los porcentajes no cambian. La escala se mantiene al filtrar y hacer zoom.<br>Gris: sin dato. Demografía: estimación espacial.${isBirthRegionMetric(s.metric)?'<br>% de residentes estimados; ver definición SCB sobre los mapas.':''}</small>`;
}

/** Keep the scale visible and secondary explanations available on demand. */
export function compactLegend(html:string){
 return html.replace(/<small>([\s\S]*?)<\/small>/g, '<details class="legend-notes"><summary>Detalles</summary><small>$1</small></details>');
}
export function legend(s:State,rows:District[]){return compactLegend(legendContent(s,rows));}
