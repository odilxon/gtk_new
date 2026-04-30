'use client';

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { DICTS, type Dict, type Lang } from './dictionaries';

const STORAGE_KEY = 'lang';
const DEFAULT_LANG: Lang = 'uz';

type Path<T, P extends string = ''> = T extends string
  ? P
  : {
      [K in keyof T & string]: Path<T[K], P extends '' ? K : `${P}.${K}`>;
    }[keyof T & string];

export type TKey = Path<Dict>;

type Params = Record<string, string | number>;

interface I18nContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: TKey, params?: Params) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function resolve(dict: Dict, key: string): string | undefined {
  const value = key
    .split('.')
    .reduce<unknown>((acc, k) => (acc as Record<string, unknown>)?.[k], dict);
  return typeof value === 'string' ? value : undefined;
}

function format(template: string, params?: Params): string {
  if (!params) return template;
  let out = template;
  for (const [k, v] of Object.entries(params)) {
    out = out.replaceAll(`{${k}}`, String(v));
  }
  return out;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(DEFAULT_LANG);

  // SSR рендерит DEFAULT_LANG; на клиенте читаем сохранённый выбор.
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as Lang | null;
      if (saved && saved in DICTS && saved !== DEFAULT_LANG) {
        setLangState(saved);
      }
    } catch {
      /* localStorage недоступен — игнорируем */
    }
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang;
    }
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* noop */
    }
  }, []);

  const t = useCallback(
    (key: TKey, params?: Params) => {
      const dict = DICTS[lang];
      const tpl = resolve(dict, key) ?? resolve(DICTS[DEFAULT_LANG], key) ?? key;
      return format(tpl, params);
    },
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used inside <I18nProvider>');
  return ctx;
}

export function useT() {
  return useI18n().t;
}
