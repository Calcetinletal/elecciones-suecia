import type {State} from '../types';
import {isDemographyMetric} from './demography';
import {normalizeParties} from './party-selection';
export function comparisonMapState(s:State,index:number):State{
 if(index===0)return {...s,view:'demography'};
 if(index===1)return {...s,view:'electoral',metric:s.electionMetric};
 const choice=index===2?s.map3:s.map4;
 if(choice.startsWith('vote:'))return {...s,view:'electoral',metric:'party',party:normalizeParties(choice.slice(5))};
 if(['winning_party','winning_block','turnout_pct'].includes(choice))return {...s,view:'electoral',metric:choice};
 return {...s,view:'demography',metric:isDemographyMetric(choice)?choice:'mean_net_income'};
}
export function clearMunicipality(s:State){s.municipality='';s.county='';s.district='';}
