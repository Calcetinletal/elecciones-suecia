export type Language = 'es' | 'en' | 'sv';
export const languageNames: Record<Language,string> = {es:'Español',en:'English',sv:'Svenska'};
export const locales: Record<Language,string> = {es:'es-ES',en:'en-GB',sv:'sv-SE'};
export function readLanguage(search = typeof location === 'undefined' ? '' : location.search): Language {
  const p = new URLSearchParams(search);
  const requested = p.get('lang') ?? p.get('locale')?.split('-')[0];
  if (requested && Object.hasOwn(languageNames,requested)) return requested as Language;
  try {const saved = localStorage.getItem('atlas-language');if(saved && Object.hasOwn(languageNames,saved))return saved as Language;} catch { /* Storage may be disabled. */ }
  return 'es';
}
export function rememberLanguage(language: Language) {
  try {localStorage.setItem('atlas-language',language);} catch { /* URL remains the fallback. */ }
}
export function languageUrl(href: string, language: Language): string {
  const url = new URL(href,location.href);
  url.searchParams.set('lang',language);
  if(url.searchParams.has('locale'))url.searchParams.set('locale',locales[language]);
  return url.href;
}
