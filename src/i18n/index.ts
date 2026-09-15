import catalog from './messages.txt?raw';
import {readLanguage,rememberLanguage,languageNames,locales,languageUrl,type Language} from './language';
export {readLanguage,locales,languageUrl};
const language = readLanguage();
const entries = catalog.replace(/^\uFEFF/,'').split(/\r?\n/).filter(line=>line.trim()&&!line.trimStart().startsWith('#')).map(line=>line.split('|||'));
const dictionary = new Map(entries.map(([es,en,sv])=>[es,{en,sv}]));
const escapePattern = (s:string)=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const pattern = new RegExp([...dictionary.keys()].sort((a,b)=>b.length-a.length).map(key=>`${/^[\p{L}\p{Nd}_]/u.test(key)?'(?<![\\p{L}\\p{Nd}_])':''}${escapePattern(key)}${/[\p{L}\p{Nd}_]$/u.test(key)?'(?![\\p{L}\\p{Nd}_])':''}`).join('|'),'gu');
/** Translate only presentation text, never data keys, HTML markup or statistical values.
 * A single pass prevents translated words being translated again. Long messages
 * take precedence over fragments used around interpolated names and numbers. */
export function translate(text:string,target:Language=language):string {
  return target==='es'?text:text.replace(pattern,source=>dictionary.get(source)?.[target]??source);
}
export function languagePicker():string {
  return `<label class="language-picker" translate="no"><svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true"><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6h14M5 18h14"/></svg><span class="sr-only">${language==='en'?'Language':language==='sv'?'Språk':'Idioma'}</span><select id="language" aria-label="${language==='en'?'Language':language==='sv'?'Språk':'Idioma'}">${Object.entries(languageNames).map(([code,name])=>`<option lang="${code}" value="${code}" ${code===language?'selected':''}>${name}</option>`).join('')}</select></label>`;
}
const attributes = ['title','aria-label','placeholder','alt','label'];
const ignore = 'script,style,code,pre,[translate="no"]';
function localizeNode(node:Node) {
  if(node.nodeType===Node.TEXT_NODE){
    if(!node.parentElement?.closest(ignore)&&node.nodeValue){const text=translate(node.nodeValue);if(text!==node.nodeValue)node.nodeValue=text;}
    return;
  }
  if(!(node instanceof Element)||node.matches(ignore))return;
  for(const attr of attributes){const text=node.getAttribute(attr);if(text){const next=translate(text);if(next!==text)node.setAttribute(attr,next);}}
  if(node instanceof HTMLAnchorElement&&node.hasAttribute('href')){
    const url=new URL(node.href,location.href);
    if(url.origin===location.origin&&url.pathname.startsWith(import.meta.env.BASE_URL)&&!node.hasAttribute('download')&&!/\.[a-z0-9]+$/i.test(url.pathname)&&!node.getAttribute('href')?.startsWith('#')){
      const next=languageUrl(url.href,language);if(node.href!==next)node.href=next;
    }
  }
  for(const child of node.childNodes)localizeNode(child);
}
/** Legacy string-rendered panels and MapLibre popups share this presentation layer.
 * Observe only text/content attributes, not map animation geometry or styles. */
export function startLocalization() {
  document.documentElement.lang=language;
  rememberLanguage(language);
  document.title=translate(document.title);
  const description=document.querySelector('meta[name="description"]');
  if(description)description.setAttribute('content',translate(description.getAttribute('content')??''));
  const observer=new MutationObserver(records=>{
    observer.disconnect();
    const nodes=new Set<Node>();
    for(const record of records){if(record.type==='childList')record.addedNodes.forEach(n=>nodes.add(n));else nodes.add(record.target);}
    for(const node of nodes)if(node.isConnected)localizeNode(node);
    observe();
  });
  const observe=()=>observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:[...attributes,'href']});
  localizeNode(document.body);observe();
  document.addEventListener('change',event=>{
    const select=event.target as HTMLSelectElement;
    if(select.id!=='language')return;
    const next=select.value as Language;if(!Object.hasOwn(languageNames,next))return;
    rememberLanguage(next);
    // Reload the same URL so chart modules use the new number/country locale.
    // Current district, camera, filters and historical selections are retained.
    location.assign(languageUrl(location.href,next));
  });
}
