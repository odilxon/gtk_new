'use client';

import { useMemo } from 'react';

import { useI18n } from './I18nProvider';

const LOCALES: Record<string, string> = {
  uz: 'ru-RU', // в узбекском кириллическом UI используем ru-RU числовое форматирование
  ru: 'ru-RU',
  en: 'en-US',
};

export function useFormatters() {
  const { lang, t } = useI18n();
  const locale = LOCALES[lang] ?? 'ru-RU';

  return useMemo(() => {
    function formatPrice(value: number | null | undefined): string {
      if (value === null || value === undefined) return '—';
      let n = Number(value);
      let suffix = '';
      if (n >= 1000) {
        n = n / 1000;
        suffix = ` ${t('format.thousand')}`;
      }
      if (n >= 1000) {
        n = n / 1000;
        suffix = ` ${t('format.million')}`;
      }
      if (n >= 1000) {
        n = n / 1000;
        suffix = ` ${t('format.billion')}`;
      }
      return n.toLocaleString(locale, { maximumFractionDigits: 2 }) + suffix;
    }

    function formatMass(value: number | null | undefined): string {
      if (value === null || value === undefined) return '—';
      let n = Number(value);
      let suffix = ` ${t('format.kg')}`;
      if (n >= 1000) {
        n = n / 1000;
        suffix = ` ${t('format.t')}`;
      }
      if (n >= 1000) {
        n = n / 1000;
        suffix = ` ${t('format.kt')}`;
      }
      return n.toLocaleString(locale, { maximumFractionDigits: 2 }) + suffix;
    }

    function formatThousand(value: number | null | undefined): string {
      if (value === null || value === undefined) return '—';
      return Number(value).toLocaleString(locale, { maximumFractionDigits: 2 });
    }

    return { formatPrice, formatMass, formatThousand };
  }, [locale, t]);
}
