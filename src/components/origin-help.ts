import {isIncomeMetric,incomeDefinition,incomeEstimateNote} from '../utils/income';
import {socioMetric,socioMetrics} from '../utils/socio';
import {metricGroups,demographicLabel,birthRegionNote,isBirthRegionMetric} from '../utils/demography';
import {escapeHtml as e} from '../utils/format';
export const originDefinitions:Record<string,string>={
 mean_net_income:incomeDefinition,
 ...Object.fromEntries(socioMetrics.map(m=>[`socio_${m.id}_pct`,m.universe])),
 common_origin:'El grupo de nacimiento fuera de Suecia con más residentes: Europa excepto Suecia, o resto del mundo + desconocido. No exige superar el 50 % de toda la población.',
 foreign_background_pct:'Nacidos fuera de Suecia o nacidos en Suecia con ambos progenitores nacidos fuera. No incluye a los nacidos en Suecia con solo un progenitor nacido fuera.',
 foreign_born_pct:'Nacidos fuera de Suecia, aunque tengan ciudadanía sueca. En este indicador la fuente incluye país de nacimiento desconocido.',
 foreign_citizens_pct:'Residentes sin ciudadanía sueca, con independencia del lugar de nacimiento. La fuente incluye apátridas y ciudadanía desconocida.',
 born_sweden_pct:'Nacidos en Suecia, también si uno o ambos progenitores nacieron fuera.',
 born_europe_ex_sweden_pct:'Nacidos en Europa excepto Suecia. En la clasificación distrital SCB incluye Rusia y Turquía.',
 born_rest_world_unknown_pct:'Nacidos en el resto del mundo y personas cuyo país de nacimiento se desconoce. No separa África y Asia.',
};
export const originBrief:Record<string,string>={
 foreign_background_pct:'Nacidos fuera + nacidos en Suecia con dos progenitores nacidos fuera; % de todos los residentes.',
 foreign_born_pct:'Nacidos fuera de Suecia, de cualquier país, más nacimiento desconocido; % de todos los residentes.',
 foreign_citizens_pct:'Sin ciudadanía sueca, independientemente de dónde nacieron; % de todos los residentes.',
 born_sweden_pct:'Nacidos en Suecia, cualquiera que sea el origen de sus padres; % de todos los residentes.',
 born_europe_ex_sweden_pct:'Nacidos en Europa fuera de Suecia; incluye Rusia y Turquía; % de todos los residentes.',
 born_rest_world_unknown_pct:'Nacidos fuera de Europa + país de nacimiento desconocido; % de todos los residentes.',
 common_origin:'Grupo extranjero de nacimiento más numeroso: Europa sin Suecia o resto del mundo + desconocido.',
};
export function metricExplanation(metric:string){return socioMetric(metric)?.description??originDefinitions[metric]??'';}
export function mapVariableHelp(metric:string){return `<details class="map-variable-help"><summary aria-label="Qué mide este indicador" title="Qué mide este indicador">i</summary><div><strong>${e(demographicLabel(metric))}</strong><p>${e(metricExplanation(metric))}</p>${originBrief[metric]?`<p>${e(originBrief[metric])}</p>`:''}<small>Estimación distrital a partir de áreas SCB.</small></div></details>`;}
export function demographyHelp(metric:string,municipality='',county=''){
 const socio=socioMetric(metric);if(socio)return `<div class="indicator-help"><details class="district-birth-notice"><summary>Qué mide este indicador</summary><p><strong>${e(socio.label)}:</strong> ${e(socio.description)}</p><p>Estimación DeSO → distrito. Consulta el año junto al mapa y la evolución en «Renta y sociedad · historia».</p></details><a class="parents-link" href="${import.meta.env.BASE_URL}methodology/#socio-history">Fuentes y método ↗</a></div>`;
 if(isIncomeMetric(metric))return `<div class="indicator-help income-help"><details class="district-birth-notice"><summary>Qué mide la renta</summary><p>${e(incomeDefinition)}</p><p>${e(incomeEstimateNote)}</p><p>La cuadrícula poblacional de 2025 pondera la renta de 2024 en el mapa 2026. No se supone que sean ingresos de 2026.</p></details><a class="parents-link" href="${import.meta.env.BASE_URL}methodology/#income">Renta · fuentes y método ↗</a></div>`;
 const params=new URLSearchParams({country:'PARENT_MIXED'});if(municipality)params.set('municipality',municipality);else if(county)params.set('county',county);
 return `<div class="indicator-help"><details class="district-birth-notice"><summary><span class="indicator-brief">${e(originBrief[metric]??'Qué mide este indicador')}</span><span class="indicator-details-link">Definición y ejemplos</span></summary><p><strong>${e(demographicLabel(metric))}:</strong> ${e(originDefinitions[metric]??'')}</p>${metric==='foreign_background_pct'?'<p>Incluye países europeos y no europeos, con cualquier ciudadanía. Nacidos en Suecia con un progenitor nacido en Suecia y otro fuera se clasifican como origen sueco, no extranjero.</p>':''}<details class="definition-list"><summary>Ver todas las definiciones</summary><dl>${metricGroups[0].metrics.map(([key])=>`<dt>${e(demographicLabel(key))}</dt><dd>${e(originDefinitions[key])}</dd>`).join('')}<dt>Nacidos en Suecia · un progenitor nacido fuera</dt><dd>Un progenitor nació en Suecia y el otro en el extranjero. SCB lo clasifica como «origen sueco». Se muestra por municipio en Nacimiento de los padres.</dd></dl><p>Ejemplo: alguien nacido en Suecia de dos padres nacidos en Siria y con ciudadanía sueca tiene origen extranjero, pero no nació fuera ni tiene ciudadanía extranjera.</p></details><p>${isBirthRegionMetric(metric)?birthRegionNote:'Los porcentajes usan todos los residentes de la tabla correspondiente. La demografía por distrito es una estimación espacial.'} Las categorías se solapan: no se suman. Nacimiento no significa ciudadanía, etnia o religión.</p><p><strong>¿África y Asia por separado?</strong> Están disponibles por municipio en Países y Evolución. La tabla de áreas pequeñas usada para estimar los distritos solo separa Suecia, Europa y resto del mundo; el detalle municipal no permite saber su reparto dentro de cada distrito.</p><a href="${import.meta.env.BASE_URL}methodology/">Fuentes y método</a></details><a class="parents-link" href="${import.meta.env.BASE_URL}countries/?${params}">Nacimiento de los padres · municipios ↗</a></div>`;
}
