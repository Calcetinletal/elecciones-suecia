import parties from '../../config/parties.json';
import {partyIds,partyLabel} from '../utils/party-selection';
import {partyBadge} from '../utils/categories';
import {escapeHtml as e} from '../utils/format';

export function openPartyPicker(selection:string,onApply:(selection:string)=>void,onClose:()=>void){
 document.querySelector('#party-picker')?.remove();
 const selected=new Set(partyIds(selection)),dialog=document.createElement('dialog');
 dialog.id='party-picker';dialog.setAttribute('aria-labelledby','party-picker-title');
 dialog.innerHTML=`<form method="dialog"><header><h2 id="party-picker-title">Sumar partidos</h2><button value="cancel" aria-label="Cerrar">×</button></header><p>Marca uno o varios partidos para sumar su voto.</p><div class="party-picker-grid">${parties.map(p=>`<label style="--party:${p.color}" title="${e(p.name)}"><input type="checkbox" name="sum-party" value="${p.id}" ${selected.has(p.id)?'checked':''}>${partyBadge(p.id)}<span>${e(p.id==='other'?'Otros':p.id)}</span></label>`).join('')}</div><p class="party-sum-definition">Suma de votos / total de votos válidos. No cambia el mapa de origen.</p><footer><output aria-live="polite"></output><button id="apply-party-sum" value="apply">Aplicar suma</button></footer></form>`;
 document.querySelector('#app')!.append(dialog);
 const choices=()=>[...dialog.querySelectorAll<HTMLInputElement>('input:checked')].map(input=>input.value).join('+');
 const refresh=()=>{const chosen=choices();dialog.querySelector('output')!.textContent=chosen?partyLabel(chosen):'Selecciona al menos un partido';dialog.querySelector<HTMLButtonElement>('#apply-party-sum')!.disabled=!chosen;};
 dialog.addEventListener('change',refresh);
 dialog.addEventListener('close',()=>{const chosen=choices(),apply=dialog.returnValue==='apply';dialog.remove();if(apply&&chosen)onApply(chosen);else onClose();},{once:true});
 refresh();dialog.showModal();dialog.querySelector<HTMLInputElement>('input')!.focus();
}
