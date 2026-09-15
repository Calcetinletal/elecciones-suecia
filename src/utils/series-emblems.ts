import shapes from '../assets/origin-shapes.json';
import {escapeHtml as e} from './format';
const paths=shapes as Record<string,string>;
const globe='<circle cx="50" cy="50" r="36" fill="none" stroke="currentColor" stroke-width="5"/><ellipse cx="50" cy="50" rx="17" ry="36" fill="none" stroke="currentColor" stroke-width="4"/><path d="M15 50h70M22 31h56M22 69h56" fill="none" stroke="currentColor" stroke-width="4"/>';
export function originEmblem(code:string){
 const parent=code.startsWith('PARENT_');
 const path=paths[code]??(parent?paths[code==='PARENT_FOREIGN_BORN'?'WORLD':'SE']:code==='REG_UNASSIGNED'?null:paths.WORLD);
 const family=parent&&code!=='PARENT_FOREIGN_BORN'?`<g fill="currentColor" stroke="white" stroke-width="2"><circle cx="68" cy="63" r="9"/><path d="M55 91v-8a13 13 0 0 1 26 0v8Z"/><circle cx="87" cy="63" r="9" ${code==='PARENT_MIXED'?'fill="white" stroke="currentColor"':''}/><path d="M74 91v-8a13 13 0 0 1 26 0v8Z" ${code==='PARENT_MIXED'?'fill="white" stroke="currentColor"':''}/></g>`:'';
 return `<span class="series-emblem origin-emblem" aria-hidden="true"><svg viewBox="0 0 100 100" focusable="false">${path?`<path d="${path}" fill="currentColor" ${parent?'opacity=".6"':''}/>`:globe}${family}</svg></span>`;
}
export function politicalEmblem(code:string){
 if(code==='other')return '<span class="series-emblem" aria-hidden="true"><svg viewBox="0 0 40 40"><circle cx="10" cy="20" r="3" fill="currentColor"/><circle cx="20" cy="20" r="3" fill="currentColor"/><circle cx="30" cy="20" r="3" fill="currentColor"/></svg></span>';
 return `<span class="series-emblem political-emblem" aria-hidden="true"><img src="${import.meta.env.BASE_URL}assets/parties/${e(code)}.${code==='S'||code==='SD'?'png':'svg'}" alt="" loading="lazy"></span>`;
}
/** Pick the higher-contrast black/white label for the saturated card background. */
export function seriesInk(color:string){
 let rgb:number[];
 if(color.startsWith('#'))rgb=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16)/255);
 else{const values=color.match(/[\d.]+/g)?.map(Number)??[0,45,48];const [h,s,l]=[values[0]/360,values[1]/100,values[2]/100];const a=s*Math.min(l,1-l);rgb=[0,8,4].map(n=>{const k=(n+h*12)%12;return l-a*Math.max(-1,Math.min(k-3,9-k,1));});}
 const linear=rgb.map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);const lum=linear[0]*.2126+linear[1]*.7152+linear[2]*.0722;
 return lum>.179?'#000000':'#ffffff';
}
