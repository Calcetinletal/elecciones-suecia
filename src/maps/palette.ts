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
export function numericMetric(s:State){return s.metric.startsWith('delta_')?s.metric:s.view==='demography'?s.metric:s.metric==='turnout_pct'?'turnout_pct':`pct_${s.party}`;}
export function label(s:State){
 if(s.view==='compare')return demographicLabel(s.metric)+' / '+comparisonElectionLabel(s);
 if(s.metric==='winning_block')return 'Bloque más votado';
 if(s.metric==='common_origin')return 'Región extranjera predominante ≈';
 if(s.metric.startsWith('delta_')&&s.view==='electoral')return 'Cambio 2022 → 2026 · '+s.metric.replace('delta_pct_','voto ').replace('delta_turnout_pct','participación');
 return s.view==='bivariate'?`Origen extranjero × voto ${s.party}`:s.view==='dominant'||s.metric==='winning_party'?'Partido ganador':s.metric==='turnout_pct'?'Participación electoral':isBirthRegionMetric(s.metric)?demographicLabel(s.metric):s.metric==='foreign_born_pct'?'Nacidos fuera de Suecia¹':s.metric==='foreign_citizens_pct'?'Ciudadanía extranjera¹':s.view==='demography'?'Origen extranjero':'Voto '+s.party;
}
export function legend(s:State,rows:District[]){
 if(s.metric==='winning_block'||s.metric==='common_origin'){const blocks=s.metric==='winning_block';return `<b>${e(label(s))}</b><div class="categorical-legend">${(blocks?blockDefinitions:originDefinitions).map(c=>`<span><i style="background:${c.color}"></i>${e(c.name)}</span>`).join('')}<span><i style="background:#b1aabb"></i>Empate</span><span><i style="background:#7b8793"></i>Sin dato</span></div><small>${blocks?'Agrupación analítica; suma de votos.':'Dos grupos SCB; excluye Suecia. Estimación por distrito. No identifica países individuales.'}${s.view==='compare'?'<br>Mapa derecho: % voto, de 0 a 100 %.':''}</small>`;}

 if(s.metric.startsWith('delta_')&&s.view==='electoral')return `<b>${e(label(s))}</b><div class="scale">${[-30,-20,-10,0,10,20,30].map(v=>`<i style="background:${divergent(v)}"></i>`).join('')}</div><div class="scale-labels"><span>−30 pp</span><span>0</span><span>+30 pp</span></div><small>Solo distritos comparables. Gris: límites cambiados, unidad nueva o sin comparación.</small>`;
 if(s.view==='bivariate'){const x=thresholds(rows,'foreign_background_pct'),y=thresholds(rows,`pct_${s.party}`);return `<b>Cuantiles nacionales · 3 × 3</b><div class="biv-legend"><span class="vertical">Voto ${e(s.party)} →</span><div class="biv-grid">${[...bivariate.slice(6),...bivariate.slice(3,6),...bivariate.slice(0,3)].map(c=>`<span style="background:${c}"></span>`).join('')}</div></div><span>Origen extranjero →</span><small>X: ${percent(x[0])} / ${percent(x[1])}<br>Y: ${percent(y[0])} / ${percent(y[1])}<br>Bajo ≤ primer corte; alto &gt; segundo corte.<br>Gris claro: bajo en ambos; gris oscuro: sin dato.</small>`;}
 if(s.view==='dominant'||(s.view==='electoral'&&s.metric==='winning_party'))return `<b>Partido ganador</b><div class="party-legend">${parties.map(p=>`<span>${partyBadge(p.id)}${p.id==='other'?'Otros':''}</span>`).join('')}</div><small>Gris: sin resultado · Lila: empate.</small>`;
 return `<b>${e(label(s))}</b><div class="scale">${[0,10,20,30,40,50,60,70,80,90,100].map(v=>`<i style="background:${sequential(v)}"></i>`).join('')}</div><div class="scale-labels"><span>0 %</span><span>50 %</span><span>100 %</span></div><small>Gris: sin dato. Demografía: estimación espacial.${isBirthRegionMetric(s.metric)?'<br>% de residentes estimados; ver definición SCB sobre los mapas.':''}</small>`;
}
