import type {State} from '../types';
import {normalizeParties,partyLabel} from './party-selection';
export const dominantOptions:[string,string][]=[['winning_party','Partido dominante'],['winning_block','Bloque dominante']];
export function electionSelection(s:State){const metric=s.view==='compare'?s.electionMetric:s.metric;return dominantOptions.some(([key])=>key===metric)?metric:s.party;}
export function comparisonElectionKey(s:State){return s.electionMetric==='party'?`pct_${s.party}`:s.electionMetric;}
export function comparisonElectionLabel(s:State){return dominantOptions.find(([key])=>key===s.electionMetric)?.[1]??`Voto ${partyLabel(s.party)}`;}
export function selectElection(s:State,selection:string){
 if(s.view==='cartogram')s.cartogramMode='voters';
 const dominant=dominantOptions.some(([key])=>key===selection);
 if(!dominant)s.party=normalizeParties(selection);
 if(s.view==='compare')s.electionMetric=dominant?selection:'party';
 else s.metric=dominant?selection:'party';
}
