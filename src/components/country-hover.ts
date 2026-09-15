import {originEmblem} from '../utils/series-emblems';
import {escapeHtml as e,percent} from '../utils/format';
import {countryLabel,countryShare,type BirthCountry,type BirthRegion} from '../utils/countries';
import {leadingOrigin,originColor,originTitle} from '../utils/origins';
export function originBadge(c:BirthCountry){return `<span class="origin-badge map-origin-emblem" style="--origin:${originColor(c.code)}">${originEmblem(c.code)}</span>`;}
export function countryHover(r:BirthRegion,items:BirthCountry[],regions:boolean,selected?:BirthCountry){
 const lead=leadingOrigin(r,items,regions),top=selected?[selected]:lead.ranked.slice(0,3),color=originColor(selected?.code??lead.code);
 return `<article class="hover-card mini-hover" style="--accent:${color}"><header><h3>${e(r.name)}</h3><p>${r.level==='national'?'Suecia':r.level==='county'?'Región':'Municipio'} · SCB 2025</p></header><section><div class="hover-section-title"><span>${selected?.kind==='parent'?'Nacimiento propio y padres':selected?'Origen seleccionado':regions?'Mayores subtotales':'Países más comunes publicados'}</span></div>${!selected&&!lead.category?`<small>${e(originTitle(lead))}</small>`:''}<div class="origin-ranking">${top.map(c=>`<div>${originBadge(c)}<span>${e(countryLabel(c))}</span><b>${percent(countryShare(r,c))}</b></div>`).join('')}</div><small>% de residentes.${regions?' Subtotales incompletos.':!selected?' Suecia excluida.':''}</small></section><footer>Pulsa para ver el detalle</footer></article>`;
}
