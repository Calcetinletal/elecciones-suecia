import type {State} from '../types';

const views = [
 {id:'electoral',label:'Resultados electorales',hint:'Ver el voto a cada partido y los ganadores por distrito',icon:'<path d="M8 9 5 11v9h14v-9l-3-2M9 13h6M9 3h6v7H9z"/><path d="m10.5 6 1 1 2-2"/>'},
 {id:'demography',label:'Población y sociedad',hint:'Origen, socioeconomía y demografía por distrito',icon:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6.5h14M5 17.5h14"/>'},
 {id:'compare',label:'Comparar mapas',hint:'Comparar de dos a cuatro mapas sincronizados',icon:'<rect x="2" y="4" width="8" height="16" rx="1.5"/><rect x="14" y="4" width="8" height="16" rx="1.5"/><path d="m4 16 2-4 2 2m8-5 2 3 2-2"/>'},
] as const;

export function viewTabs(state:State){
 return `<div class="view-tabs"><div class="primary-views" role="group" aria-label="Tipo de mapa">${views.map(v=>`<button type="button" class="view-choice" data-view="${v.id}" aria-pressed="${state.view===v.id}" title="${v.hint}"><svg class="view-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${v.icon}</svg><span>${v.label}</span></button>`).join('')}</div><details class="more-maps" ${['bivariate','dominant'].includes(state.view)?'open':''}><summary>Más mapas</summary><div><button data-view="bivariate" aria-pressed="${state.view==='bivariate'}">Cruce voto y origen</button><button data-view="dominant" aria-pressed="${state.view==='dominant'}">Ganador por origen</button></div></details></div>`;
}
