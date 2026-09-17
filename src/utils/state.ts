import {readLanguage,locales} from '../i18n/language';
import {normalizeParties} from './party-selection';
import {isDemographyMetric} from './demography';
import type {State} from '../types';
export const defaults:State={cartogramLayout:'compact',cartogramMode:'voters',mapCount:2,map3:'mean_net_income',map4:'socio_education_pct',year:2026,view:'electoral',metric:'winning_party',electionMetric:'party',party:'SD',county:'',municipality:'',district:'',band:'all',weight:'votes',locale:'es-ES',quality:'all',size:'equal',analysisY:'party',analysisX:'foreign_background_pct',lng:16,lat:62.7,zoom:4.2};
export function readState(search=location.search):State{
 const p=new URLSearchParams(search),s={...defaults};
 const aliases:Record<string,string>={foreign_background:'foreign_background_pct',foreign_born:'foreign_born_pct',foreign_citizens:'foreign_citizens_pct'};if(aliases[p.get('metric')??''])p.set('metric',aliases[p.get('metric')!]);if(!p.has('view')&&p.get('metric')?.startsWith('foreign_'))p.set('view','demography');
 for(const key of Object.keys(s) as (keyof State)[]){const v=p.get(key);if(v!==null)(s as unknown as Record<string,unknown>)[key]=typeof defaults[key]==='number'?Number(v):v;}
 if(!['electoral','demography','bivariate','dominant','compare','cartogram'].includes(s.view))s.view='electoral';
 if(!['geography','voters','shares'].includes(s.cartogramMode))s.cartogramMode='voters';
 if(!['compact','geographic'].includes(s.cartogramLayout))s.cartogramLayout='compact';
 s.party=normalizeParties(s.party);
 if(![2,3,4].includes(s.mapCount))s.mapCount=2;
 for(const key of ['map3','map4'] as const){if(s[key].startsWith('vote:'))s[key]='vote:'+normalizeParties(s[key].slice(5));else if(!isDemographyMetric(s[key])&&!['winning_party','winning_block','turnout_pct'].includes(s[key]))s[key]=defaults[key];}
 if(!isDemographyMetric(s.metric)&&!['winning_party','winning_block','party','turnout_pct','foreign_background_pct','foreign_born_pct','foreign_citizens_pct','delta_pct_S','delta_pct_SD','delta_pct_M','delta_turnout_pct'].includes(s.metric))s.metric='winning_party';
 if(!['party','winning_party','winning_block'].includes(s.electionMetric))s.electionMetric='party';
 if(!['2022','2026'].includes(String(s.year)))s.year=2022;
 s.locale=locales[readLanguage(search)];
 if(!['votes','equal'].includes(s.weight))s.weight='votes';
 if(!['all','high'].includes(s.quality))s.quality='all';
 if(!['all','0','10','20','30','40','50'].includes(s.band))s.band='all';
 if(!isDemographyMetric(s.analysisX)||s.analysisX==='common_origin')s.analysisX='foreign_background_pct';
 if(!['party','turnout'].includes(s.analysisY))s.analysisY='party';
 if(!['votes','equal'].includes(s.size))s.size='equal';
 for(const k of ['lat','lng','zoom'] as const)if(!Number.isFinite(s[k]))s[k]=defaults[k];
 s.lat=Math.max(54,Math.min(70,s.lat));s.lng=Math.max(5,Math.min(33,s.lng));s.zoom=Math.max(2,Math.min(16,s.zoom));
 if(['demography','compare'].includes(s.view)&&!isDemographyMetric(s.metric))s.metric='foreign_background_pct';
 if(s.view==='cartogram'&&isDemographyMetric(s.metric))s.metric='winning_party';
 if(s.year===2022&&s.metric.startsWith('delta_'))s.metric='party';
 return s;
}
export function writeState(s:State){const p=new URLSearchParams();for(const[k,v]of Object.entries(s))if(v!=='')p.set(k,String(v));history.replaceState(null,'',`${location.pathname}?${p}`);}
export function routeUrl(route:string,s:State){const p=new URLSearchParams();for(const[k,v]of Object.entries(s))if(v!=='')p.set(k,String(v));return `${import.meta.env.BASE_URL}${route}?${p}`;}
