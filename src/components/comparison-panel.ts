import type {District,State} from '../types';
import {parties} from '../maps/palette';
import {demographicLabel} from '../utils/demography';
import {partyBadge} from '../utils/categories';
import {escapeHtml as e,number,percent} from '../utils/format';
import {finite,sum,turnout,weightedMean} from '../utils/data';

const birthGroups=[
 {key:'born_sweden',name:'Suecia',color:'#527faf'},
 {key:'born_europe_ex_sweden',name:'Europa excepto Suecia',color:'#8661c5'},
 {key:'born_rest_world_unknown',name:'Resto + desconocido',color:'#d77947'},
];
/** Use one common, complete birthplace denominator for all three categories. */
export function comparisonValues(rows:District[],weight:string,metric='foreign_background_pct'){
 const birthRows=rows.filter(d=>finite(d.birth_regions_population)&&d.birth_regions_population>0&&birthGroups.every(g=>finite(d[g.key+'_count'])));
 const population=sum(birthRows,'birth_regions_population');
 const origins=birthGroups.map(g=>({...g,pct:population?100*(sum(birthRows,g.key+'_count')??0)/population:null}));
 const votes=parties.map(p=>({...p,pct:weightedMean(rows,'pct_'+p.id,weight)}));
 const demographic=(key:string)=>{const known=rows.filter(d=>finite(d[key])&&finite(d.population)&&d.population>0),denom=sum(known,'population');return denom?known.reduce((n,d)=>n+(d[key] as number)*d.population!,0)/denom:null;};
 return {origins,votes,population,birthDistricts:birthRows.length,turnout:turnout(rows),foreignBackground:demographic('foreign_background_pct'),selectedDemography:demographic(metric)};
}
export function comparisonPanel(visible:District[],s:State,selected?:District){
 const rows=selected?[selected]:visible,extraMetric=['foreign_born_pct','foreign_citizens_pct'].includes(s.metric)?s.metric:'foreign_background_pct',data=comparisonValues(rows,s.weight,extraMetric);
 const title=selected?.district_name??(s.municipality?rows[0]?.municipality_name:s.county?rows[0]?.county_name:'Suecia')??'Sin distritos';
 const scope=selected?`${selected.municipality_name} · ${selected.district_id}`:`${number(rows.length)} distritos`;
 const municipality=selected?.municipality_code??s.municipality;
 const municipalButton=municipality?'<button id="municipal-context" class="comparison-detail-button municipal-context-button" aria-controls="municipal-inline" aria-expanded="false">Origen municipal</button>':'';
 const provisional=rows.some(d=>d.election_status==='provisional');
 const year=rows[0]?.birth_regions_year??rows[0]?.demography_year??'—';
 if(selected)return `<div class="comparison-data comparison-chart-data"><header class="comparison-scope"><div><h2>${e(title)}</h2><p>${e(scope)} · Participación ${percent(data.turnout)} · Límites históricos variables</p></div><button id="close-district" aria-label="Cerrar ficha">×</button></header><section class="district-history comparison-history" data-district-history aria-label="Evolución de votos y origen poblacional"></section><section id="municipal-inline" class="municipal-context municipal-compact" data-municipal-context hidden></section><div class="comparison-actions">${municipalButton}<button id="comparison-detail" class="comparison-detail-button">Fuentes, tablas y detalle ↗</button></div></div>`;
 return `<div class="comparison-data">
 <header class="comparison-scope"><div><h2>${e(title)}</h2><p>${e(scope)}</p></div>${selected?'<button id="close-district" aria-label="Cerrar ficha">×</button>':''}</header>
 <section class="comparison-votes" aria-label="Datos electorales"><header><h3>Elecciones · ${s.year}</h3><span>${provisional?'Provisional':''}</span></header>
 <div class="comparison-party-grid">${data.votes.map(p=>`<div class="comparison-party" style="--party:${p.color}" title="${e(p.name)}">${partyBadge(p.id)}<b>${percent(p.pct)}</b></div>`).join('')}</div>
 <div class="comparison-inline"><span>Participación <b>${percent(data.turnout)}</b></span><small>${s.weight==='votes'?'% de votos válidos':'Media distrital'}</small></div></section>
 <section class="comparison-population" aria-label="Datos poblacionales"><header><h3>Nacimiento · ${year} ≈</h3><span>${number(data.population)} residentes ≈</span></header>
 <div class="comparison-origin-list">${data.origins.map(g=>`<div style="--origin:${g.color}"><i></i><span>${e(g.name)}</span><b>${percent(g.pct)}</b></div>`).join('')}</div>
 <div class="comparison-inline"><span>${e(demographicLabel(extraMetric))} ≈ <b>${percent(data.selectedDemography)}</b></span>${data.birthDistricts<rows.length?'<small>Datos parciales</small>':''}</div>
 <p class="comparison-definition">Europa incluye Rusia y Turquía. Resto incluye país desconocido.</p></section>
 <section id="municipal-inline" class="municipal-context municipal-compact" data-municipal-context hidden></section><div class="comparison-actions">${municipalButton}<button id="comparison-detail" class="comparison-detail-button">Ver detalle y evolución ↗</button></div><p class="comparison-select-hint">Pulsa un distrito para ver las dos evoluciones.</p>
 </div>`;
}
