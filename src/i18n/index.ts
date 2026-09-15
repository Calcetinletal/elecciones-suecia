import {languageFlag} from './flags';
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
 const label=language==='en'?'Language':language==='sv'?'Språk':'Idioma';
 return `<details class="language-picker" translate="no"><summary id="language" data-current-language="${language}" aria-label="${label}: ${languageNames[language]}">${languageFlag(language)}<span>${languageNames[language]}</span><svg class="language-chevron" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><div class="language-menu" role="group" aria-label="${label}">${Object.entries(languageNames).map(([code,name])=>`<button type="button" data-language="${code}" lang="${code}" aria-pressed="${code===language}">${languageFlag(code as Language)}<span>${name}</span><span class="language-check" aria-hidden="true">${code===language?'✓':''}</span></button>`).join('')}</div></details>`;
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
  document.addEventListener('click',event=>{
    const target=event.target as Element;
    const button=target.closest<HTMLButtonElement>('[data-language]');
    const picker=document.querySelector<HTMLDetailsElement>('.language-picker');
    if(!button){if(!target.closest('.language-picker')&&picker)picker.open=false;return;}
    const next=button.dataset.language as Language;if(!Object.hasOwn(languageNames,next))return;
    if(next===language){if(picker)picker.open=false;document.getElementById('language')?.focus();return;}
    rememberLanguage(next);
    // Keep the current district, filters, camera and historical selections.
    location.assign(languageUrl(location.href,next));
  });
  document.addEventListener('keydown',event=>{
    const picker=document.querySelector<HTMLDetailsElement>('.language-picker');
    if(event.key==='Escape'&&picker?.open){picker.open=false;document.getElementById('language')?.focus();}
  });
}
