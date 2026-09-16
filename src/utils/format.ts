export const escapeHtml=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export let locale='es-ES';
export function setLocale(value:string){locale=value;}
export function number(v:unknown,digits=0){return typeof v==='number'&&Number.isFinite(v)?new Intl.NumberFormat(locale,{maximumFractionDigits:digits}).format(v):'Sin dato';}
export const percent=(v:unknown)=>typeof v==='number'&&Number.isFinite(v)?`${number(v,1)} %`:'Sin dato';
export function method(value:string){return value==='exact_valdistrikt'?'SCB exacto por valdistrikt':value==='population_weighted_estimate'?'Estimación DeSO → valdistrikt · ponderada por población':value==='areal_estimate'?'Estimación DeSO → valdistrikt · por área':value==='mixed_spatial_estimate'?'Estimación espacial mixta':'Sin dato demográfico';}
export async function compressedJSON<T>(url:string):Promise<T>{
 const response=await fetch(url,{cache:'no-cache'});
 if(!response.ok)throw new Error(`No se pudo cargar ${url} (${response.status})`);
 // Fetch automatically decodes Content-Encoding: gzip (Vite), while static hosts
 // may serve the .gz file as an opaque binary. Inspect the received bytes, not
 // the header, which can remain present after the browser has decoded the body.
 const buffer=await response.arrayBuffer();
 if(!buffer.byteLength)throw new Error(`Respuesta vacía: ${url}`);
 const signature=new Uint8Array(buffer,0,Math.min(2,buffer.byteLength));
 if(signature[0]===0x1f&&signature[1]===0x8b){
  const stream=new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).json() as Promise<T>;
 }
 return new Response(buffer).json() as Promise<T>;
}
