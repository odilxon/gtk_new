'use client';

import { useEffect, useState } from 'react';

import { TnvedMultiSelect } from '@/components/charts/TnvedMultiSelect';
import { Button, Input, Select } from '@/components/ui';
import {
  useCategories,
  useCountries,
  useProducts,
} from '@/hooks/useLookups';
import { useT } from '@/i18n/I18nProvider';
import type { GTKListParams, Regime } from '@/types/api';

interface Props {
  value: GTKListParams;
  onApply: (next: GTKListParams) => void;
}

export function GTKFilters({ value, onApply }: Props) {
  const t = useT();
  const [open, setOpen] = useState(true);
  const [draft, setDraft] = useState<GTKListParams>(value);
  const { data: countries = [] } = useCountries();
  const { data: categories = [] } = useCategories();
  const { data: products = [] } = useProducts(draft.category_id);

  const REGIME_OPTIONS = [
    { value: 'ИМ', label: `ИМ (${t('totals.import')})` },
    { value: 'ЭК', label: `ЭК (${t('totals.export')})` },
  ];

  // Если внешний `value` сменился (например, при пагинации) — подтягиваем
  // только page/page_size, чтобы не терять незакоммиченные правки фильтров.
  useEffect(() => {
    setDraft((d) => ({
      ...d,
      page: value.page,
      page_size: value.page_size,
    }));
  }, [value.page, value.page_size]);

  const set = <K extends keyof GTKListParams>(key: K, v: GTKListParams[K]) =>
    setDraft((d) => ({ ...d, [key]: v }));

  const apply = () => onApply({ ...draft, page: 1 });

  const reset = () => {
    const cleared: GTKListParams = { page: 1, page_size: value.page_size };
    setDraft(cleared);
    onApply(cleared);
  };

  const activeCount = [
    draft.regime,
    draft.country_id,
    draft.category_id,
    draft.product_id,
    draft.date_from,
    draft.date_to,
    draft.search,
    draft.tnved?.length,
  ].filter((v) => v !== undefined && v !== '' && v !== 0).length;

  // Есть ли несохранённые правки, которые ждут «Янгилаш».
  const dirty =
    draft.regime !== value.regime ||
    draft.country_id !== value.country_id ||
    draft.category_id !== value.category_id ||
    draft.product_id !== value.product_id ||
    draft.date_from !== value.date_from ||
    draft.date_to !== value.date_to ||
    (draft.search ?? '') !== (value.search ?? '') ||
    JSON.stringify(draft.tnved ?? []) !== JSON.stringify(value.tnved ?? []);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          <span className="font-medium text-gray-900">{t('filters.title')}</span>
          {activeCount > 0 && (
            <span className="text-xs text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
              {activeCount}
            </span>
          )}
          {dirty && (
            <span className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
              {t('filters.notApplied')}
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-gray-100">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              apply();
            }}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              <Select
                label={t('filters.regime')}
                placeholder={t('filters.allRegimes')}
                options={REGIME_OPTIONS}
                value={draft.regime ?? ''}
                onChange={(e) =>
                  set('regime', (e.target.value || undefined) as Regime | undefined)
                }
              />
              <Select
                label={t('filters.country')}
                placeholder={t('filters.allCountries')}
                options={countries.map((c) => ({ value: c.id, label: c.name }))}
                value={draft.country_id ?? ''}
                onChange={(e) =>
                  set('country_id', e.target.value ? Number(e.target.value) : undefined)
                }
              />
              <Select
                label={t('filters.category')}
                placeholder={t('filters.allCategories')}
                options={categories.map((c) => ({ value: c.id, label: c.name }))}
                value={draft.category_id ?? ''}
                onChange={(e) =>
                  set('category_id', e.target.value ? Number(e.target.value) : undefined)
                }
              />
              <Select
                label={t('filters.product')}
                placeholder={t('filters.allProducts')}
                options={products.map((p) => ({ value: p.id, label: p.name }))}
                value={draft.product_id ?? ''}
                onChange={(e) =>
                  set('product_id', e.target.value ? Number(e.target.value) : undefined)
                }
              />
              <div className="sm:col-span-2">
                <TnvedMultiSelect
                  label={t('filters.tnved')}
                  value={draft.tnved ?? []}
                  onChange={(codes) =>
                    set('tnved', codes.length > 0 ? codes : undefined)
                  }
                />
              </div>
              <Input
                label={t('filters.dateFrom')}
                type="date"
                value={draft.date_from ?? ''}
                onChange={(e) => set('date_from', e.target.value || undefined)}
              />
              <Input
                label={t('filters.dateTo')}
                type="date"
                value={draft.date_to ?? ''}
                onChange={(e) => set('date_to', e.target.value || undefined)}
              />
              <div className="sm:col-span-2 lg:col-span-4">
                <Input
                  label={t('common.search')}
                  type="text"
                  placeholder={t('filters.searchPlaceholder')}
                  value={draft.search ?? ''}
                  onChange={(e) => set('search', e.target.value || undefined)}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-4">
              <Button type="submit" variant="primary">
                {t('common.apply')}
              </Button>
              <Button type="button" variant="secondary" onClick={reset}>
                {t('common.reset')}
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
