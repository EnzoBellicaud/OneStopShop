import { Injectable, signal } from '@angular/core';
import { TRANSLATIONS } from './translations';

export interface SupportedLocale {
  code: string;
  label: string;
}

export const SUPPORTED_LOCALES: SupportedLocale[] = [
  { code: 'en', label: 'English' },
  { code: 'it', label: 'Italiano' },
  { code: 'fr', label: 'Français' },
];

const FALLBACK_LOCALE = 'en';
const STORAGE_KEY = 'oss.locale';

@Injectable({ providedIn: 'root' })
export class TranslationService {
  /** Reactive current locale. Read it (directly or via the pipe) to re-render on change. */
  readonly locale = signal<string>(FALLBACK_LOCALE);

  readonly locales = SUPPORTED_LOCALES;

  constructor() {
    const saved = localStorage.getItem(STORAGE_KEY);
    const browser = navigator.language?.slice(0, 2);
    this.setLocale(this.resolve(saved || browser));
  }

  private resolve(code: string | null | undefined): string {
    return SUPPORTED_LOCALES.some(l => l.code === code) ? (code as string) : FALLBACK_LOCALE;
  }

  setLocale(code: string): void {
    const resolved = this.resolve(code);
    this.locale.set(resolved);
    document.documentElement.lang = resolved;
    localStorage.setItem(STORAGE_KEY, resolved);
  }

  /**
   * Translate a dot-separated key for the active locale, falling back to English
   * then to the key itself. `params` interpolates {placeholders}.
   */
  translate(key: string, params?: Record<string, string | number>): string {
    const current = this.locale();
    const value =
      this.lookup(TRANSLATIONS[current], key) ??
      this.lookup(TRANSLATIONS[FALLBACK_LOCALE], key) ??
      key;
    if (params) {
      return value.replace(/\{(\w+)\}/g, (_, p) => String(params[p] ?? `{${p}}`));
    }
    return value;
  }

  private lookup(dict: unknown, key: string): string | undefined {
    let node: unknown = dict;
    for (const part of key.split('.')) {
      if (node && typeof node === 'object' && part in (node as Record<string, unknown>)) {
        node = (node as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }
    return typeof node === 'string' ? node : undefined;
  }
}
