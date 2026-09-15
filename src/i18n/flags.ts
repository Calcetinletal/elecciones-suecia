import type {Language} from './language';
/** Inline vectors render consistently on Windows, which may show flag emoji as letters. */
export function languageFlag(language:Language):string {
 const shapes:Record<Language,string>={
  es:'<path fill="#aa151b" d="M0 0h60v40H0z"/><path fill="#f1bf00" d="M0 10h60v20H0z"/><path fill="#aa151b" d="M16 16h8v9a4 4 0 0 1-8 0z"/><path fill="#f8e7bc" d="M17 17h3v4h-3zm4 4h2v4h-2z"/><path fill="#aa151b" d="M16 13h8v2h-8z"/>',
  en:'<path fill="#012169" d="M0 0h60v40H0z"/><path stroke="#fff" stroke-width="9" d="m0 0 60 40M60 0 0 40"/><path stroke="#c8102e" stroke-width="3" d="m0 0 60 40M60 0 0 40"/><path stroke="#fff" stroke-width="13" d="M30 0v40M0 20h60"/><path stroke="#c8102e" stroke-width="7" d="M30 0v40M0 20h60"/>',
  sv:'<path fill="#006aa7" d="M0 0h60v40H0z"/><path fill="#fecc00" d="M18 0h8v40h-8z"/><path fill="#fecc00" d="M0 16h60v8H0z"/>'
 };
 return `<svg class="language-flag" data-flag="${language}" viewBox="0 0 60 40" width="27" height="18" aria-hidden="true" focusable="false">${shapes[language]}</svg>`;
}
