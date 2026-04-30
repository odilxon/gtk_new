'use client';

import { useI18n } from '@/i18n/I18nProvider';
import { LANGS } from '@/i18n/dictionaries';
import { cn } from '@/lib/cn';

export function LanguageSwitcher() {
  const { lang, setLang } = useI18n();
  return (
    <div className="inline-flex items-center rounded-lg bg-gray-100 p-0.5">
      {LANGS.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => setLang(l.code)}
          className={cn(
            'px-2.5 py-1 text-xs font-medium rounded-md transition-colors',
            lang === l.code
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-900',
          )}
          aria-pressed={lang === l.code}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
