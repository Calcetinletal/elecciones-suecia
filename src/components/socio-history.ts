import type {District,State} from '../types';
import {compressedJSON,escapeHtml as e,number} from '../utils/format';
import {socioMetrics,socioValue,socioAmount,aggregateSocio,type SocioPoint} from '../utils/socio';
import {archiveDistrictChain,type DistrictArchive} from '../utils/district-series';
type Bundle={area:Record<string,SocioPoint[]>;districts:Record<string,Record<string,Record<string,SocioPoint[]>>>};
const base=import.meta.env.BASE_URL;
const bundles=new Map<string,Promise<Bundle>>();
function bundle(code:string){let pending=bundles.get(code);if(!pending){pending=compressedJSON<Bundle>(`${base}data/history/socio/${encodeURIComponent(code)}.json.gz`).catch(error=>{bundles.delete(code);throw error;});bundles.set(code,pending);}return pending;}
export function districtSocioSeries(d:District,archive:DistrictArchive,data:Bundle,metric:string):SocioPoint[]{
 const chain=archiveDistrictChain(d,archive);return chain.flatMap(segment=>{
  const histories=segment.rows.map(r=>data.districts[String(segment.year)]?.[r.district_id]?.[metric]??[]);
  const years=[...new Set(histories.flatMap(rows=>rows.map(r=>r.year)))].sort((a,b)=>a-b);
  return years.map(year=>({...aggregateSocio(histories.map(rows=>rows.find(r=>r.year===year)),year,metric==='population'),geometry:segment.year,scope:segment.rows.map(r=>r.district_name).join(' + '),comparable:!chain.some(part=>part.breakBefore),method:year<2015?'whole_deso':'population_grid'}));
 });
}
export async function mountSocioHistory(root:HTMLElement,s:State,d?:District,areaName?:string){
 const code=d?.municipality_code??s.municipality??'',areaCode=code||s.county||'00';
 root.innerHTML='<p role="status">Cargando historia socioeconómica…</p>';
 try{
  const [data,archive,index]=await Promise.all([bundle(areaCode),d?compressedJSON<DistrictArchive>(`${base}data/history/district_archive/${encodeURIComponent(code)}.json.gz`):Promise.resolve(null),fetch(`${base}data/history/socio/index.json`,{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('Índice socioeconómico');return r.json();})]);
  if(!root.isConnected)return;
  let metric='income',active=0,observations:SocioPoint[]=[];
  const scope=d?`${d.district_name} · ${d.municipality_name}`:s.municipality?`${areaName??s.municipality} · Municipio completo`:s.county?`${areaName??s.county} · Región completa`:'Suecia · País completo';
  root.innerHTML=`<header class="socio-heading"><div><strong>${e(scope)}</strong><small>${d?'Distrito · estimaciones históricas':'Ámbito completo · no solo los distritos filtrados'}</small></div><button type="button" data-socio-close aria-label="Cerrar">×</button></header><div class="socio-controls"><label>Serie histórica<select data-socio-metric>${socioMetrics.map(m=>`<option value="${m.id}">${e(m.label)} · ${m.years.join('–')}</option>`).join('')}</select></label><button type="button" data-socio-download>↓ CSV</button></div><p class="socio-universe"></p><div class="socio-readout"><strong></strong><span></span></div><svg class="socio-chart" viewBox="0 0 680 235" role="img"></svg><label class="socio-year">Año<input type="range" data-socio-year><output></output></label><p class="socio-geography"></p><details class="socio-notes"><summary>Fuentes y comparabilidad</summary><p>Las líneas unen observaciones disponibles; no rellenan años sin dato. La renta usa precios de 2024. Los distritos siguen los límites de cada edición, no un territorio constante. Hasta 2014 solo se estiman uniones de áreas DeSO completas; desde 2015 se usan cuadrículas anuales. Cambios: edad de educación en 2023, DeSO en 2024 y CKM de población en 2025.</p><p>Empleo: ocupados / población de 20–64 años. Desempleo: desempleados / población activa de 20–64 años. Ambos usan BAS desde 2020, sin unirlos a RAMS. Los agregados BAS municipales y regionales suman DeSO; las demás series usan el agregado publicado por SCB.</p><a data-socio-source target="_blank" rel="noreferrer">SCB ↗</a> · <a href="${base}data/history/socio/provenance.json">Cobertura y método ↗</a></details><details class="socio-table"><summary>Ver datos en tabla</summary><div class="table-wrap"></div></details>`;
  function readout(){
   const def=socioMetrics.find(m=>m.id===metric)!,point=observations[active],v=point?socioValue(point,def.factor):null;
   root.querySelector<HTMLAnchorElement>('[data-socio-source]')!.href=metric==='education'&&(point?.year??0)>=2024?index.sources.education_new:index.metrics[metric].url;
   root.querySelector('.socio-readout strong')!.textContent=socioAmount(v,def.unit);
   root.querySelector('.socio-readout span')!.textContent=point?`${point.year}${d?' ≈':''}`:'Sin observaciones enlazadas';
   root.querySelector('.socio-year output')!.textContent=point?String(point.year):'—';
   const slider=root.querySelector<HTMLInputElement>('[data-socio-year]')!;slider.value=String(active);slider.setAttribute('aria-valuetext',point?String(point.year):'Sin dato');
   root.querySelector('.socio-geography')!.textContent=point?.geometry?`Límites ${point.geometry} · ${point.scope}${point.year<2015?' · Solo áreas DeSO completas':''}${point.comparable===false?' · Enlace territorial no verificado':''}`:point?.method==='sum_deso'?'Agregado de áreas DeSO · celdas protegidas':d?'No se ha podido enlazar este distrito con ediciones que tengan esta serie.':'Agregado publicado por SCB';
   root.querySelectorAll<SVGCircleElement>('[data-socio-point]').forEach(c=>c.setAttribute('r',Number(c.dataset.socioPoint)===active?'5':'3'));
  }
  function draw(){
   const def=socioMetrics.find(m=>m.id===metric)!;
   observations=d&&archive?districtSocioSeries(d,archive,data,metric):data.area[metric]??[];active=Math.max(0,observations.length-1);
   root.dataset.metric=metric;root.dataset.scope=d?'district':areaCode;root.dataset.observations=String(observations.filter(p=>socioValue(p,def.factor)!==null).length);
   root.querySelector('.socio-universe')!.textContent=def.universe;
   const points=observations.flatMap((p,i)=>{const v=socioValue(p,def.factor);return v===null?[]:[{p,i,v}];});
   const minYear=observations[0]?.year??def.years[0],maxYear=observations.at(-1)?.year??def.years[1];
   const max=Math.max(1,...points.map(p=>p.v)),top=max*1.1;
   const x=(year:number)=>minYear===maxYear?365:76+(year-minYear)/(maxYear-minYear)*576,y=(v:number)=>200-v/top*179;
   const svg=root.querySelector('svg')!;svg.setAttribute('aria-label',`${def.label} · ${scope}`);
   svg.innerHTML=`<title>${e(def.label)} · ${e(scope)}</title>${[0,.25,.5,.75,1].map(f=>`<line x1="76" x2="652" y1="${y(f*top)}" y2="${y(f*top)}" stroke="#dfe7ec"/><text x="67" y="${y(f*top)+4}" text-anchor="end">${def.unit==='SEK'?number(f*top/1000,0)+'k':number(f*top,def.unit==='%'?1:0)}${def.unit==='%'?' %':''}</text>`).join('')}${[...new Set([minYear,Math.round((minYear+maxYear)/2),maxYear])].map(year=>`<text x="${x(year)}" y="225" text-anchor="middle">${year}</text>`).join('')}${points.length?`<polyline points="${points.map(p=>`${x(p.p.year)},${y(p.v)}`).join(' ')}" fill="none" stroke="${def.color}" stroke-width="3"/>${points.map(p=>`<circle data-socio-point="${p.i}" cx="${x(p.p.year)}" cy="${y(p.v)}" r="3" fill="${def.color}"><title>${p.p.year}: ${e(socioAmount(p.v,def.unit))}</title></circle>`).join('')}`:'<text x="340" y="110" text-anchor="middle">Sin observaciones disponibles</text>'}`;
   const slider=root.querySelector<HTMLInputElement>('[data-socio-year]')!;slider.min='0';slider.max=String(Math.max(0,observations.length-1));slider.step='1';slider.disabled=observations.length<2;
   const source=root.querySelector<HTMLAnchorElement>('[data-socio-source]')!;source.href=index.metrics[metric].url;
   root.querySelector('.table-wrap')!.innerHTML=`<table><thead><tr><th>Año</th><th>${e(def.label)} · ${e(def.unit)}</th><th>Ámbito</th></tr></thead><tbody>${observations.map(p=>`<tr><td>${p.year}</td><td>${socioAmount(socioValue(p,def.factor),def.unit)}</td><td>${p.geometry?`Límites ${p.geometry} · ${e(p.scope)}`:e(scope)}</td></tr>`).join('')}</tbody></table>`;readout();
  }
  root.querySelector('[data-socio-metric]')!.addEventListener('change',event=>{metric=(event.target as HTMLSelectElement).value;draw();});
  root.querySelector('[data-socio-year]')!.addEventListener('input',event=>{active=Number((event.target as HTMLInputElement).value);readout();});
  root.querySelector('svg')!.addEventListener('pointermove',event=>{const target=(event.target as Element).closest<SVGCircleElement>('[data-socio-point]');if(target){active=Number(target.dataset.socioPoint);readout();}});
  root.querySelector('[data-socio-close]')!.addEventListener('click',()=>{root.closest<HTMLDetailsElement>('details')!.open=false;});
  root.querySelector('[data-socio-download]')!.addEventListener('click',()=>{
   const def=socioMetrics.find(m=>m.id===metric)!,csv=['year,value,unit,geometry_year,numerator,denominator',...observations.map(p=>[p.year,socioValue(p,def.factor)??'',def.unit,p.geometry??'',p.n??'',p.d??''].join(','))].join('\n');
   const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=`history-${d?.district_id??areaCode}-${metric}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  root.addEventListener('keydown',event=>{if(event.key==='Escape'){const menu=root.closest<HTMLDetailsElement>('details')!;menu.open=false;menu.querySelector('summary')?.focus();}});
  draw();root.dataset.ready='true';
 }catch(error){if(root.isConnected)root.innerHTML=`<p role="alert">No se pudo cargar la historia: ${e(String(error))}</p><button data-socio-retry>Reintentar</button>`;root.querySelector('[data-socio-retry]')?.addEventListener('click',()=>void mountSocioHistory(root,s,d,areaName));}
}
