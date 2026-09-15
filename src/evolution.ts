import {readLanguage} from './i18n/language';
import {countryLabel} from './utils/countries';
import type {District} from './types';
import {birthObservation,voteObservation,districtBirthSeries,archiveDistrictChain,archiveBirthRows,type DistrictArchive} from './utils/district-series';
import {originEmblem,politicalEmblem,seriesInk} from './utils/series-emblems';
import {originColor} from './utils/origins';
import {compressedJSON,escapeHtml as e,number,percent} from './utils/format';
import parties from '../config/parties.json';

type Category={code:string;name_es?:string;name_sv:string;description?:string;kind:string};
type Series={code:string;name:string;color:string;description?:string;party?:boolean;emblem?:string};
type Observation={year:number;scope_label?:string;population?:number|null;total?:number|null;counts:Record<string,number|null>;pct?:Record<string,number|null>;missing?:Record<string,number>;status?:string;ckm?:boolean;unavailable_reason?:string;reported_units?:number;expected_units?:number};
type Measure='votes'|'parents'|'birth';
type Territory={code:string;votes:Observation[];parents:Observation[];birth:Observation[];breaks:Partial<Record<Measure,number[]>>};
type Index={regions:{code:string;name:string;level:string}[];parents:Category[];countries:Category[];groups:Category[];source_updated_2026:string;sources:Record<string,string>};
const base=import.meta.env.BASE_URL;
const colors=['#6f55bf','#da8031','#219b8e','#487bbd','#c54f82','#74863b','#697985','#925642'];
const groupColors:Record<string,string>=Object.fromEntries(['REG_AFRICA','REG_ASIA','REG_EUROPE_EX_SE','REG_AMERICAS','REG_OCEANIA','REG_UNASSIGNED','REG_NON_EUROPE'].map(code=>[code,originColor(code)]));
const parentNames:Record<string,string>={PARENT_FOREIGN_BORN:'Nacidos fuera de Suecia',PARENT_BOTH_FOREIGN:'Nacidos en Suecia · dos padres fuera',PARENT_MIXED:'Nacidos en Suecia · un padre fuera',PARENT_BOTH_SWEDEN:'Nacidos en Suecia · dos padres en Suecia'};
const name=(c:Category)=>countryLabel(c);
const value=(r:Observation,s:string)=>r.pct?r.pct[s]??null:typeof r.counts[s]==='number'&&r.population?100*r.counts[s]!/r.population:null;

/** Solid lines connect available observations; source values and comparability notes stay unchanged. */
function timeline(root:HTMLElement,rows:Observation[],series:Series[],breaks:number[],title:string,compact=false,initialYear?:number,breakLabels:Record<string,string>={}){
 if(!rows.length){root.innerHTML='<p class="empty-history">No hay observaciones de origen para este ámbito. La fuente por áreas pequeñas empieza en 2010.</p>';return;}
 let active=initialYear===undefined?rows.length-1:Math.max(0,rows.findIndex(r=>r.year===initialYear)),pinned=active;const selected=new Set(series.map(s=>s.code));
 const W=compact?460:800,H=compact?260:320,left=48,right=22,top=18,bottom=36;
 const firstYear=rows[0].year,lastYear=rows.at(-1)!.year;
 const x=(year:number)=>firstYear===lastYear?(left+W-right)/2:left+(year-firstYear)/(lastYear-firstYear)*(W-left-right);
 const yearTicks=[...new Set(rows.length<=7?rows.map(r=>r.year):(compact?[firstYear,2006,2010,2014,2018,2022,lastYear]:[firstYear,2006,2010,2014,2018,2022,lastYear]).filter(year=>year>=firstYear&&year<=lastYear))];
 root.innerHTML=`<div class="timeline-heading"><span>${e(title)}</span><output class="timeline-year" aria-live="polite"></output></div><p class="timeline-universe"></p><p class="timeline-geography" hidden></p><svg class="timeline-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${e(title)}: porcentajes a lo largo del tiempo. Usa el selector de año o la tabla para consultar valores."></svg><label class="timeline-scrubber"><span>Año</span><input type="range" min="0" max="${rows.length-1}" value="${active}" step="1" ${rows.length===1?'disabled':''} aria-label="Año de ${e(title)}"><output></output></label><p class="timeline-hint">${rows.length===1?'Una observación disponible · todavía no muestra una evolución':'Cada tarjeta corresponde a una línea · pulsa para ocultarla'}</p><div class="timeline-legend" aria-label="Mostrar u ocultar series">${series.map(s=>`<button type="button" class="series-card ${s.party?'series-card-party':'series-card-origin'}" data-series="${e(s.code)}" aria-pressed="true" title="${e(s.description??s.name)}" style="--series:${s.color};--series-ink:${seriesInk(s.color)}"><span class="series-identity" style="background-color:${s.color};color:${seriesInk(s.color)}">${s.party?politicalEmblem(s.code):originEmblem(s.emblem??s.code)}<span class="series-title">${e(s.party?(s.code==='other'?'Otros':s.code):s.name)}</span></span><span class="series-value"><b class="series-amount"></b><small></small></span></button>`).join('')}</div><details class="timeline-coverage" hidden><summary>Datos parciales · qué significa</summary><p>Algunos países no tienen un dato individual publicado. Los porcentajes regionales suman solo los datos disponibles; no representan el total completo. «Sin dato» no significa cero.</p><ul></ul></details>${breaks.length?`<details class="history-scope-help"><summary>Comparabilidad entre años</summary><ul>${[...new Set(breaks)].filter(b=>b>firstYear&&b<lastYear).sort((a,b)=>a-b).map(b=>`<li>${e(breakLabels[String(b)]??(compact?`${Math.floor(b)}–${Math.ceil(b)}: comparabilidad territorial no verificada`:`Cambio territorial: ${b}`))}</li>`).join('')}</ul><p>Las líneas conectan los valores disponibles; no garantizan un territorio constante.</p></details>`:''}<details class="timeline-table"><summary>Ver datos en tabla</summary><div class="table-wrap"></div></details>`;
 const svg=root.querySelector<SVGSVGElement>('svg')!,slider=root.querySelector<HTMLInputElement>('input')!;
 function readout(){
  const row=rows[active];const geography=root.querySelector<HTMLElement>('.timeline-geography')!;geography.hidden=!row.scope_label;geography.textContent=row.scope_label??'';root.querySelector('.timeline-universe')!.textContent=row.population?`${number(row.population)} residentes · ${row.year}`:row.total?`${number(row.total)} votos válidos · ${row.year}`:row.unavailable_reason??'Sin denominador publicado';root.querySelector('.timeline-year')!.textContent=`${row.year}${row.status==='provisional'?' · provisional':row.ckm?' · CKM':''}`;
  slider.value=String(active);slider.setAttribute('aria-valuetext',String(row.year));root.querySelector('.timeline-scrubber output')!.textContent=String(row.year);
  for(const s of series){const button=[...root.querySelectorAll<HTMLButtonElement>('[data-series]')].find(b=>b.dataset.series===s.code)!;button.querySelector('.series-amount')!.textContent=percent(value(row,s.code));button.querySelector('small')!.textContent=row.missing?.[s.code]&&value(row,s.code)!==null?'Parcial':'';button.title=`${s.description??s.name} · ${row.year}: ${percent(value(row,s.code))}${row.missing?.[s.code]?` · ${row.missing[s.code]} países/categorías sin dato individual`:''}`;button.setAttribute('aria-pressed',String(selected.has(s.code)));}
  const coverage=root.querySelector<HTMLDetailsElement>('.timeline-coverage')!;coverage.hidden=!series.some(s=>row.missing?.[s.code]);coverage.querySelector('ul')!.innerHTML=series.filter(s=>row.missing?.[s.code]).map(s=>`<li>${e(s.name)}: ${row.missing![s.code]} países/categorías sin dato individual en ${row.year}.</li>`).join('');
  svg.querySelectorAll<SVGCircleElement>('circle[data-year]').forEach(point=>{const current=Number(point.dataset.year)===row.year;point.setAttribute('r',current?'5':rows.length<10?'3.5':'2');point.setAttribute('fill',current?'white':point.getAttribute('stroke')!);point.setAttribute('stroke-width',current?'3':'1.5');});
  const line=svg.querySelector('.timeline-cursor');line?.setAttribute('x1',String(x(row.year)));line?.setAttribute('x2',String(x(row.year)));
 }
 function draw(){
  const visible=series.filter(s=>selected.has(s.code));const max=Math.max(5,...rows.flatMap(r=>visible.map(s=>value(r,s.code)??0)));const step=[1,2,5,10,20,25].find(step=>max/step<=4)??25;const ceiling=Math.min(100,Math.ceil((max+step*.15)/step)*step);const y=(v:number)=>H-bottom-v/ceiling*(H-top-bottom);
  const ticks=Array.from({length:Math.floor(ceiling/step)+1},(_,i)=>i*step);
  const paths=visible.map(s=>{
   const points=rows.flatMap(r=>{const v=value(r,s.code);return v!==null&&Number.isFinite(v)?[{row:r,value:v}]:[];});
   return `<g data-line-series="${e(s.code)}" aria-label="${e(s.name)}">${points.map(({row:r,value:v},i)=>{
    const previous=points[i-1];
    const line=previous?`<line x1="${x(previous.row.year)}" y1="${y(previous.value)}" x2="${x(r.year)}" y2="${y(v)}" stroke="${s.color}" stroke-width="3.2" stroke-linecap="round"/>`:'';
    return `${line}<circle data-year="${r.year}" cx="${x(r.year)}" cy="${y(v)}" r="${rows.length<10?4:2.8}" fill="${s.color}" stroke="${s.color}" stroke-width="1.8"><title>${e(s.name)} · ${r.year}: ${percent(v)}</title></circle>`;
   }).join('')}</g>`;
  }).join('');
  svg.innerHTML=`<title>${e(title)}</title><desc>Porcentaje por año. Las líneas continuas unen los puntos disponibles, incluso entre años sin dato o con cambios territoriales. No añaden observaciones ni garantizan límites constantes. Los datos provisionales y CKM se identifican al consultar cada año.</desc>${ticks.map(t=>`<line x1="${left}" x2="${W-right}" y1="${y(t)}" y2="${y(t)}" stroke="#e5ecf0"/><text x="${left-10}" y="${y(t)+4}" text-anchor="end" fill="#6a7d89" font-size="14">${t} %</text>`).join('')}${yearTicks.map(t=>`<text x="${x(t)}" y="${H-9}" text-anchor="middle" fill="#6a7d89" font-size="14">${t}</text>`).join('')}${paths}<line class="timeline-cursor" x1="${x(rows[active].year)}" x2="${x(rows[active].year)}" y1="${top}" y2="${H-bottom}" stroke="#183b55" stroke-opacity=".3"/>`;
  root.querySelector('.table-wrap')!.innerHTML=`<table><caption>${e(title)} · % · ${e(series.some(s=>s.party)?'votos válidos':'todos los residentes')}</caption><thead><tr><th>Año</th>${visible.map(s=>`<th scope="col">${e(s.name)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr><th scope="row">${r.year}${r.status==='provisional'?' *':r.ckm?' †':''}${r.scope_label?`<small class="history-table-scope">${e(r.scope_label)}</small>`:''}</th>${visible.map(s=>`<td>${percent(value(r,s.code))}${r.missing?.[s.code]?` <small>(${r.missing[s.code]} sin desglose)</small>`:''}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  readout();
 }
 slider.addEventListener('input',()=>{active=Number(slider.value);pinned=active;readout();});
 svg.addEventListener('pointermove',event=>{const bounds=svg.getBoundingClientRect();const year=firstYear+((event.clientX-bounds.left)/bounds.width*W-left)/(W-left-right)*(lastYear-firstYear);active=rows.reduce((best,r,i)=>Math.abs(r.year-year)<Math.abs(rows[best].year-year)?i:best,0);readout();});
 svg.addEventListener('pointerleave',()=>{active=pinned;readout();});
 svg.addEventListener('click',()=>{pinned=active;});
 const legend=root.querySelector<HTMLElement>('.timeline-legend')!;
 function highlight(code?:string){svg.querySelectorAll<SVGGElement>('[data-line-series]').forEach(line=>{line.style.opacity=code&&line.dataset.lineSeries!==code?'.16':'1';});}
 legend.addEventListener('pointerover',event=>highlight((event.target as HTMLElement).closest<HTMLElement>('[data-series]')?.dataset.series));
 legend.addEventListener('pointerleave',()=>highlight());
 legend.addEventListener('focusin',event=>highlight((event.target as HTMLElement).closest<HTMLElement>('[data-series]')?.dataset.series));
 legend.addEventListener('focusout',()=>highlight());
 root.querySelector('.timeline-legend')!.addEventListener('click',event=>{const button=(event.target as HTMLElement).closest<HTMLButtonElement>('[data-series]');if(!button)return;const code=button.dataset.series!;if(selected.has(code)){if(selected.size===1)return;selected.delete(code);}else selected.add(code);draw();});
 draw();
}

export async function showEvolution(root:HTMLElement){
 if(new URLSearchParams(location.search).get('scope')==='district'){await showDistrictArchive(root);return;}
 root.innerHTML='<p class="loading" role="status">Cargando series históricas oficiales…</p>';
 try{
  const response=await fetch(`${base}data/history/index.json`);if(!response.ok)throw new Error(`Índice histórico (${response.status})`);const index=await response.json() as Index;
  const params=new URLSearchParams(location.search);let code=index.regions.some(r=>r.code===params.get('municipality'))?params.get('municipality')!:'00';
  let mode=['parents','regions','countries'].includes(params.get('origin')??'')?params.get('origin')!:'parents';
  let requested=(params.get('origins')??params.get('country')??'').split(',').filter(c=>index.countries.some(x=>x.code===c));
  let countryCodes=requested.length?requested.slice(0,8):['FI','SY','IQ','PL','IR'];
  let data:Territory|null=null,loadId=0;
  root.innerHTML=`<section class="evolution-page"><div class="evolution-intro"><div><span class="eyebrow">SUECIA A LO LARGO DEL TIEMPO</span><h2>Evolución</h2><p>Votos y origen poblacional, año a año.</p></div><label>Territorio<select id="history-territory"><option value="00">Suecia · nacional</option><optgroup label="Municipios">${index.regions.filter(r=>r.level==='municipality').sort((a,b)=>a.name.localeCompare(b.name,'sv')).map(r=>`<option value="${e(r.code)}" ${r.code===code?'selected':''}>${e(r.name)}</option>`).join('')}</optgroup></select></label><button id="history-csv">↓ CSV</button></div><p id="history-scope" class="history-scope"></p><div id="history-status" role="status"></div><div class="history-grid"><section class="history-card"><header><div><span class="eyebrow">RIKSDAG · % DE VOTOS VÁLIDOS</span><h3>Votos por partido</h3></div><span class="history-period">2002—2026</span></header><div id="vote-history"></div><p class="history-note" id="votes-note"></p></section><section class="history-card"><header><div><span class="eyebrow">% DE TODOS LOS RESIDENTES</span><h3>Origen poblacional</h3></div><label class="origin-history-label"><span class="sr-only">Desglose del origen poblacional</span><select id="history-origin"><option value="parents" ${mode==='parents'?'selected':''}>Nacimiento y padres</option><option value="regions" ${mode==='regions'?'selected':''}>Regiones de nacimiento</option><option value="countries" ${mode==='countries'?'selected':''}>Países de nacimiento</option></select></label></header><div id="history-country-picker" hidden><label>Añadir país<select id="history-country">${index.countries.filter(c=>c.kind==='country').sort((a,b)=>name(a).localeCompare(name(b),readLanguage())).map(c=>`<option value="${e(c.code)}">${e(name(c))}</option>`).join('')}</select></label><button id="history-add-country">Añadir</button><div id="history-country-chips"></div></div><div id="origin-history"></div><p class="history-note" id="origin-note"></p></section></div><details class="history-method"><summary>Fuentes y cómo leer los gráficos</summary><p>Las líneas unen observaciones publicadas, no son estimaciones entre años. Pulsa las leyendas para ocultar series y ajustar la escala; mueve el cursor o el selector de año para ver los porcentajes. Las líneas conectan los puntos disponibles, también cuando hay años intermedios sin dato; esos años siguen figurando como «Sin dato» en la consulta y la tabla.</p><p>Votos: elecciones al Riksdag, 2002–2022 definitivos de SCB y 2026 provisional de Valmyndigheten. Se divide el número de votos de cada partido por todos los votos válidos, incluidos los de otros partidos. FP se muestra como L. El recuento de 2026 incluye únicamente unidades que han informado; quedan unidades de recogida pendientes. Esta página es una instantánea estática.</p><p>Origen: residentes a 31 de diciembre de cada año, 2002–2025. Los cuatro grupos según nacimiento propio y de los padres son distintos y no se solapan; tener un progenitor nacido fuera y otro en Suecia se incluye en origen sueco según SCB. No son datos sobre cómo vota cada grupo. No se infiere religión ni etnia.</p><p>Desde 2025 SCB aplica protección CKM: pequeños ajustes pueden cambiar la suma de los grupos. La etiqueta CKM identifica esos datos al consultar el año. Los países pequeños pueden estar agrupados por SCB; se conserva «sin dato» y los continentes son subtotales de celdas publicadas, no totales completos. Los códigos y el reconocimiento de países también cambian con el tiempo. No deben sumarse «Fuera de Europa» y los continentes que contiene.</p><p>Regiones de nacimiento: clasificación ONU M49. Turquía y Chipre en Asia; Rusia en Europa; antigua URSS y países agrupados o desconocidos sin asignación continental. Esta definición difiere de las tres categorías SCB del mapa por distritos.</p><p>La serie usa los municipios publicados en cada año, no los límites de un distrito actual. Los cambios territoriales documentados se describen en las notas de comparabilidad: Lidingö/Vaxholm en 2011 (población de 2010, por su división de referencia). SCB ya separa Knivsta en los resultados electorales de 2002 y publica la serie de Heby con su código actual. Las cifras de población usan la división del 1 de enero siguiente al año de referencia; las elecciones, la división electoral correspondiente.</p><p>${Object.entries(index.sources).map(([k,url])=>`<a href="${e(url)}" target="_blank" rel="noreferrer">${({votes:'SCB · elecciones',parents:'SCB · nacimiento y padres',birth:'SCB · países por municipio',national_birth:'SCB · países nacional',parents_2025:'SCB · padres 2025',birth_2025:'SCB · países 2025'} as Record<string,string>)[k]??k} ↗</a>`).join(' · ')} · <a href="https://resultat.val.se/resultatfiler/val2026/">Valmyndigheten 2026 ↗</a> · <a href="${base}data/history/provenance.json">Procedencia y archivos originales</a> · <a href="${base}assets/credits.json">Créditos de los símbolos</a></p></details></section>`;
  const getSeries=():Series[]=>mode==='parents'?index.parents.map((c,i)=>({code:c.code,name:parentNames[c.code]??name(c),color:originColor(c.code),description:c.description})):mode==='regions'?index.groups.map(c=>({code:c.code,name:name(c),color:groupColors[c.code]??colors[0]})):countryCodes.map(code=>({code,name:name(index.countries.find(c=>c.code===code)!),color:originColor(code)}));
  function save(){const p=new URLSearchParams({municipality:code,origin:mode,lang:readLanguage()});if(mode==='countries')p.set('origins',countryCodes.join(','));history.replaceState(null,'',`${base}evolution/?${p}`);for(const a of document.querySelectorAll<HTMLAnchorElement>('nav a')){if(a.dataset.route===''||a.dataset.route==='countries/'){const url=new URL(a.href);url.searchParams.delete('county');url.searchParams.delete('district');if(code==='00')url.searchParams.delete('municipality');else url.searchParams.set('municipality',code);a.href=url.href;}}}
  function drawOrigin(){
   if(!data)return;
   const isCountries=mode==='countries';root.querySelector<HTMLElement>('#history-country-picker')!.hidden=!isCountries;
   root.querySelector('#history-country-chips')!.innerHTML=countryCodes.map(c=>`<button data-remove-country="${e(c)}" title="Quitar ${e(name(index.countries.find(x=>x.code===c)!))}">${e(name(index.countries.find(x=>x.code===c)!))} ×</button>`).join('');
   timeline(root.querySelector('#origin-history')!,data[mode==='parents'?'parents':'birth'],getSeries(),data.breaks[mode==='parents'?'parents':'birth']??[],'Origen poblacional');
   root.querySelector('#origin-note')!.textContent=`2002–2025 · 31 diciembre · 2025: cambio de protección SCB (CKM).${mode==='regions'?' Subtotales publicados: faltan países sin desglose.':mode==='countries'?' Sin dato: país agrupado, sin dato publicado o sin código para ese año.':''}`;save();
  }
  async function load(){
   const version=++loadId;data=null;root.querySelector('#history-status')!.textContent='Cargando territorio…';root.querySelector<HTMLButtonElement>('#history-csv')!.disabled=true;root.querySelector('.history-grid')!.setAttribute('aria-busy','true');root.querySelector('.history-grid')!.classList.add('history-loading');
   try{
    const loaded=await compressedJSON<Territory>(`${base}data/history/${encodeURIComponent(code)}.json.gz`);if(version!==loadId)return;data=loaded;
    const region=index.regions.find(r=>r.code===code)!;
    root.querySelector('#history-scope')!.innerHTML=`<strong>${e(region.name)}</strong> · ${code==='00'?'Serie nacional':'Serie municipal'}${params.has('district')?' · El distrito seleccionado pertenece a este municipio. Esta serie describe el municipio completo.':''}${Object.values(data.breaks).some(b=>b?.length)?' · Cambios territoriales descritos en las notas de comparabilidad.':''}`;
    timeline(root.querySelector('#vote-history')!,data.votes,parties.map(p=>({code:p.id,name:p.name,color:p.color,party:true})),data.breaks.votes??[],'Votos por partido');
    const latest=data.votes.at(-1)!;root.querySelector('#votes-note')!.textContent=`2026 provisional · ${number(latest.reported_units)} / ${number(latest.expected_units)} unidades con recuento · Fuente: ${index.source_updated_2026.replace('T',' ')} (Estocolmo).`;
    drawOrigin();root.querySelector('#history-status')!.textContent='';root.querySelector<HTMLButtonElement>('#history-csv')!.disabled=false;
   }catch(error){if(version===loadId){root.querySelector('#history-status')!.textContent=`No se pudo cargar la serie: ${(error as Error).message}`;root.querySelector('#vote-history')!.innerHTML='';root.querySelector('#origin-history')!.innerHTML='';}}finally{if(version===loadId){root.querySelector('.history-grid')!.setAttribute('aria-busy','false');root.querySelector('.history-grid')!.classList.remove('history-loading');}}
  }
  root.querySelector('#history-territory')!.addEventListener('change',event=>{code=(event.target as HTMLSelectElement).value;params.delete('district');void load();});
  root.querySelector('#history-origin')!.addEventListener('change',event=>{mode=(event.target as HTMLSelectElement).value;drawOrigin();});
  root.querySelector('#history-add-country')!.addEventListener('click',()=>{const next=root.querySelector<HTMLSelectElement>('#history-country')!.value;if(!countryCodes.includes(next)){if(countryCodes.length===8){root.querySelector('#history-status')!.textContent='Puedes comparar hasta 8 países. Quita uno para añadir otro.';return;}countryCodes.push(next);drawOrigin();}root.querySelector('#history-status')!.textContent='';});
  root.querySelector('#history-country-chips')!.addEventListener('click',event=>{const c=(event.target as HTMLElement).closest<HTMLButtonElement>('[data-remove-country]')?.dataset.removeCountry;if(c&&countryCodes.length>1){countryCodes=countryCodes.filter(x=>x!==c);drawOrigin();}});
  root.querySelector('#history-csv')!.addEventListener('click',()=>{
   if(!data)return;const rows:(string|number|null|undefined)[][]=[['territory_code','measure','year','category','count','denominator','pct','status','missing_country_cells']];
   for(const measure of ['votes','parents','birth'] as const)for(const r of data[measure])for(const [category,count] of Object.entries(r.counts))rows.push([code,measure,r.year,category,count,r.total??r.population,value(r,category),r.status??(r.ckm?'CKM':'published'),r.missing?.[category]]);
   const text=rows.map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n');const url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`evolucion-${code}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  await load();
 }catch(error){root.innerHTML=`<section class="empty"><h2>No se pudo abrir Evolución</h2><p>${e((error as Error).message)}</p><button onclick="location.reload()">Reintentar</button></section>`;}
}


let inlineIndex:Promise<Index>|undefined;
const inlineTerritories=new Map<string,Promise<Territory>>();
function historyIndex(){
 return inlineIndex??=(async()=>{try{const response=await fetch(`${base}data/history/index.json`);if(!response.ok)throw new Error(`Índice histórico (${response.status})`);return await response.json() as Index;}catch(error){inlineIndex=undefined;throw error;}})();
}
function historyTerritory(code:string){
 let pending=inlineTerritories.get(code);
 if(!pending){pending=compressedJSON<Territory>(`${base}data/history/${encodeURIComponent(code)}.json.gz`).catch(error=>{inlineTerritories.delete(code);throw error;});inlineTerritories.set(code,pending);}
 return pending;
}
const archives=new Map<string,Promise<DistrictArchive>>();
function districtArchive(code:string){
 let pending=archives.get(code);
 if(!pending){pending=compressedJSON<DistrictArchive>(`${base}data/history/district_archive/${encodeURIComponent(code)}.json.gz`).catch(error=>{archives.delete(code);throw error;});archives.set(code,pending);}
 return pending;
}
export async function mountDistrictHistory(root:HTMLElement,d:District){
 const code=d.municipality_code;
 const archiveURL=`${base}evolution/?scope=district&municipality=${encodeURIComponent(code)}&year=${d.election_year}&district=${encodeURIComponent(d.district_id)}`;
 root.innerHTML=`<header class="district-history-heading"><div><span class="scope-chip">Historia distrital</span><strong>${e(d.district_name)}</strong><span>Datos de cada edición · líneas continuas</span></div></header><p class="district-history-footnote" role="status">Cargando archivo histórico 2002–2026…</p><div class="district-history-charts"><section aria-label="Evolución de votos del distrito"><div data-history-votes></div></section><section aria-label="Evolución de nacimiento del distrito"><div data-history-origin></div></section></div><a class="district-archive-link" href="${archiveURL}">Explorar todos los distritos de cada elección ↗</a><details class="history-scope-help"><summary>Por qué cambia la cobertura</summary><p>Archivo electoral: 2002, 2006, 2010, 2014, 2018, 2022 y 2026. Origen: observaciones anuales desde 2010 hasta 2025. Un distrito nuevo o renumerado puede no identificarse en las ediciones anteriores; el enlace al archivo permite consultar los distritos que existían entonces.</p><p>Las líneas continuas unen todos los puntos disponibles. Si se conserva el código, se muestran también las ediciones anteriores como referencia, aunque hayan cambiado nombre o límites. La unión visual no implica que los territorios sean idénticos ni añade valores para los años sin dato. Bajo el gráfico se indica el ámbito del año consultado. Un mismo código no garantiza un territorio constante. No se han verificado correspondencias comparables anteriores a 2014–2018.</p><p>Origen: tres categorías SCB, estimadas sobre los límites de cada edición electoral. En 2010–2014 solo se publican los casos que coinciden prácticamente con áreas DeSO enteras; los demás quedan sin estimación porque no se ha incorporado una cuadrícula de población contemporánea. Desde 2015 se usan intersecciones ponderadas por la cuadrícula del propio año. Las estimaciones de baja cobertura se excluyen. En 2024 cambia la división DeSO y en 2025, la protección estadística CKM. No se inventa población de 2026.</p><p>Las fusiones comparables suman recuentos antes de calcular porcentajes. Valmyndigheten admite pequeños cambios territoriales: para 2018–2022, hasta un 5 % del electorado afectado. La cadena no equivale a una reconstrucción sobre límites fijos. Los votos son definitivos hasta 2022; 2026 es provisional.</p><p>Europa incluye Rusia y Turquía. Resto incluye país desconocido. Celdas protegidas pueden no sumar el total. No se infiere el voto de las personas según su origen.</p><p><a href="https://www.val.se/valresultat-och-statistik/statistik-och-data/radata-fran-val-2002-2022">Archivo oficial de Valmyndigheten ↗</a> · <a href="${base}data/history/annual_district_birth_provenance.json">Cobertura anual de origen ↗</a> · <a href="${base}data/history/early_district_provenance.json">Fuentes históricas ↗</a></p></details>`;
 const political=parties.map(p=>({code:p.id,name:p.name,color:p.color,party:true}));
 timeline(root.querySelector('[data-history-votes]')!,[voteObservation([d])],political,[],'Votos · % válidos',true,Number(d.election_year));
 const initialBirth=birthObservation([d]);timeline(root.querySelector('[data-history-origin]')!,Number.isFinite(initialBirth.year)&&initialBirth.year>=2010?[initialBirth]:[],districtBirthSeries,[],'Origen poblacional · % ≈',true);
 const municipalityRoot=root.closest('#panel-content, #analysis-card')?.querySelector<HTMLElement>('[data-municipal-context]');
 if(municipalityRoot)void mountMunicipalContext(municipalityRoot,code,d.municipality_name);
 try{
  const archive=await districtArchive(code);if(!root.isConnected)return;
  const chain=archiveDistrictChain(d,archive);
  const scope=(rows:District[],year:number)=>`Límites ${year} · ${rows.map(r=>`${r.district_name} (${r.district_id})`).join(' + ')}`;
  const votes=chain.map(s=>({...voteObservation(s.rows),scope_label:scope(s.rows,s.year)}));
  const births=chain.flatMap(s=>archiveBirthRows(s,archive).map(r=>({...r,scope_label:scope(s.rows,s.year)})));
  const voteBreaks=chain.flatMap((s,i)=>i&&s.breakBefore?[(chain[i-1].year+s.year)/2]:[]);
  const birthBreaks=chain.flatMap(s=>s.breakBefore?[s.year===2026?2024.5:s.year-.5]:[]);
  // Annual 2024 changes DeSO geography; do not imply method continuity across that change.
  if(births.some(r=>r.year===2014)&&births.some(r=>r.year===2015))birthBreaks.push(2014.5);
  if(births.some(r=>r.year===2024)&&births.some(r=>r.year===2023))birthBreaks.push(2023.5);
  timeline(root.querySelector('[data-history-votes]')!,votes,political,voteBreaks,'Votos · % válidos',true,Number(d.election_year));
  timeline(root.querySelector('[data-history-origin]')!,births,districtBirthSeries,birthBreaks,'Origen poblacional · % ≈',true,Number(d.birth_regions_year??d.demography_year),{'2023.5':'2024: nueva división DeSO','2014.5':'2015: comienza la ponderación por cuadrícula contemporánea'});
  const available=births.filter(r=>r.population!==null&&r.population!==undefined).length;
  root.querySelector('.district-history-footnote')!.innerHTML=`<strong>${chain.length} elecciones · ${available} años de origen con estimación</strong><span>Votos: ${votes.map(r=>r.year).join(' · ')}${births.length?` · Origen: ${births[0].year}–${births.at(-1)!.year}`:''}</span>${voteBreaks.length||birthBreaks.length?'<span>Líneas continuas entre puntos disponibles · comparabilidad territorial y de método en las notas.</span>':''}${chain[0].year>2002?'<span>El distrito no se ha podido identificar antes de '+chain[0].year+'. Consulta los distritos antiguos en el archivo.</span>':''}`;
  root.dataset.ready='true';root.dataset.district=d.district_id;root.dataset.observations=String(chain.length);root.dataset.comparable=String(chain.length>1&&!voteBreaks.length);root.dataset.territorialBreaks=String(voteBreaks.length);
 }catch(error){if(root.isConnected)root.querySelector('.district-history-footnote')!.textContent=`No se pudo cargar el archivo histórico: ${(error as Error).message}. Recarga para reintentar.`;}
}

async function showDistrictArchive(root:HTMLElement){
 root.innerHTML='<p class="loading">Cargando archivo de distritos…</p>';
 try{
  const response=await fetch(`${base}data/history/district_archive/index.json`);if(!response.ok)throw new Error(`Índice (${response.status})`);
  const index=await response.json() as {years:number[];regions:{code:string;name:string;counts:Record<string,number>}[]};
  const params=new URLSearchParams(location.search);let code=params.get('municipality')??'0180';if(!index.regions.some(r=>r.code===code))code=index.regions[0].code;
  let year=Number(params.get('year')??2026);if(!index.years.includes(year))year=2026;
  let id=params.get('district')??'',generation=0;
  root.innerHTML=`<section class="district-archive-page"><span class="eyebrow">ARCHIVO OFICIAL · 2002–2026</span><h2>Distritos de cada elección</h2><p>Consulta los distritos que existían en cada año. Los nombres, códigos y límites pueden cambiar.</p><div class="archive-selectors"><label>Municipio<select data-archive-municipality>${index.regions.slice().sort((a,b)=>a.name.localeCompare(b.name,'sv')).map(r=>`<option value="${r.code}">${e(r.name)}</option>`).join('')}</select></label><label>Elección<select data-archive-year>${index.years.map(y=>`<option value="${y}">${y}</option>`).join('')}</select></label><label>Distrito de esa edición<select data-archive-district></select></label></div><p data-archive-status role="status"></p><div data-archive-history></div><a data-municipal-history>Ver historia del municipio completo ↗</a></section>`;
  const municipalitySelect=root.querySelector<HTMLSelectElement>('[data-archive-municipality]')!,yearSelect=root.querySelector<HTMLSelectElement>('[data-archive-year]')!,districtSelect=root.querySelector<HTMLSelectElement>('[data-archive-district]')!;
  municipalitySelect.value=code;yearSelect.value=String(year);
  async function load(){
   const token=++generation;root.querySelector('[data-archive-history]')!.innerHTML='';root.querySelector('[data-archive-status]')!.textContent='Cargando distritos…';districtSelect.disabled=true;
   try{
    const archive=await districtArchive(code);if(token!==generation)return;
    const rows=archive.editions[String(year)]??[];if(!rows.some(r=>r.district_id===id))id=rows[0]?.district_id??'';
    districtSelect.innerHTML=rows.slice().sort((a,b)=>a.district_name.localeCompare(b.district_name,'sv')).map(r=>`<option value="${e(r.district_id)}">${e(r.district_name)} · ${r.district_id}</option>`).join('');districtSelect.value=id;districtSelect.disabled=!rows.length;
    root.querySelector('[data-archive-status]')!.textContent=`${rows.length} distritos publicados · ${year}`;
    const row=rows.find(r=>r.district_id===id);if(row){const host=document.createElement('section');host.className='district-history';root.querySelector('[data-archive-history]')!.replaceChildren(host);await mountDistrictHistory(host,row);}
    const link=root.querySelector<HTMLAnchorElement>('[data-municipal-history]')!;link.href=`${base}evolution/?municipality=${code}`;
    if(token===generation)history.replaceState(null,'',`${base}evolution/?${new URLSearchParams({scope:'district',municipality:code,year:String(year),district:id,lang:readLanguage()})}`);
   }catch(error){if(token===generation)root.querySelector('[data-archive-status]')!.textContent=`No se pudo cargar: ${(error as Error).message}`;}
  }
  municipalitySelect.addEventListener('change',()=>{code=municipalitySelect.value;id='';void load();});yearSelect.addEventListener('change',()=>{year=Number(yearSelect.value);void load();});districtSelect.addEventListener('change',()=>{id=districtSelect.value;void load();});await load();
 }catch(error){root.innerHTML=`<p>No se pudo abrir el archivo: ${e((error as Error).message)}</p>`;}
}

async function mountMunicipalContext(root:HTMLElement,code:string,municipality:string){
 root.innerHTML='<p class="meta" role="status">Cargando contexto municipal…</p>';
 try{
  const [index,data]=await Promise.all([historyIndex(),historyTerritory(code)]);if(!root.isConnected)return;
  let grouping='regions';
  root.innerHTML=`<header class="municipal-context-heading"><div><span class="scope-chip">Contexto municipal · otro ámbito</span><h3>${e(municipality)}</h3><p data-municipal-population></p></div><label>Composición<select aria-label="Composición del municipio"><option value="regions">Continentes</option><option value="parents">Nacimiento y padres</option></select></label></header><div class="municipal-composition"></div><p class="municipal-context-note"></p><a class="municipal-history-link" href="${base}evolution/?municipality=${encodeURIComponent(code)}">Ver evolución del municipio ↗</a>`;
  function draw(){
   const parents=grouping==='parents';const row=data[parents?'parents':'birth'].at(-1)!;
   const categories=parents?index.parents:index.groups.filter(c=>c.code!=='REG_NON_EUROPE');
   root.querySelector('[data-municipal-population]')!.textContent=`${number(row.population)} residentes · ${row.year} · todo el municipio`;
   root.querySelector('.municipal-composition')!.innerHTML=categories.map(c=>{const color=originColor(c.code);return `<div class="municipal-origin-tile" style="--series:${color};--series-ink:${seriesInk(color)}"><span class="municipal-origin-name" style="background:${color};color:${seriesInk(color)}">${originEmblem(c.code)}<span>${e(parents?parentNames[c.code]??name(c):name(c))}</span></span><span class="municipal-origin-value"><b>${percent(value(row,c.code))}</b>${row.missing?.[c.code]&&value(row,c.code)!==null?'<small>Parcial</small>':''}</span></div>`;}).join('');
   root.querySelector('.municipal-context-note')!.textContent=parents?'Cuatro grupos de nacimiento propio y de los padres, sobre todos los residentes del municipio. No describen su reparto entre distritos.': 'Subtotales de países publicados sobre todos los residentes del municipio. Suecia excluida de los continentes; los datos ocultos no son ceros. Turquía se agrupa en Asia según ONU M49.';
   root.querySelector<HTMLAnchorElement>('.municipal-history-link')!.href=`${base}evolution/?municipality=${encodeURIComponent(code)}&origin=${grouping}`;
  }
  root.querySelector('select')!.addEventListener('change',event=>{grouping=(event.target as HTMLSelectElement).value;draw();});draw();root.dataset.ready='true';root.dataset.municipality=code;
 }catch(error){if(root.isConnected)root.innerHTML=`<p class="meta">No se pudo cargar el contexto municipal: ${e((error as Error).message)}</p>`;}
}
