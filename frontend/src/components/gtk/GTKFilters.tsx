'use client';

import { useEffect, useState } from 'react';

import { TnvedMultiSelect } from '@/components/charts/TnvedMultiSelect';
import { Button, Input, Select } from '@/components/ui';
import {
  useCategories,
  useCountries,
  useProducts,
} from '@/hooks/useLookups';
import type { GTKListParams, Regime } from '@/types/api';

interface Props {
  value: GTKListParams;
  onApply: (next: GTKListParams) => void;
}

const REGIME_OPTIONS = [
  { value: 'ИМ', label: 'ИМ (Импорт)' },
  { value: 'ЭК', label: 'ЭК (Экспорт)' },
];

export function GTKFilters({ value, onApply }: Props) {
  const [open, setOpen] = useState(true);
  const [draft, setDraft] = useState<GTKListParams>(value);
  const { data: countries = [] } = useCountries();
  const { data: categories = [] } = useCategories();
  const { data: products = [] } = useProducts(draft.category_id);

  // Если внешний `value` сменился (например, страница пагинации) — синхронизируем
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

  // Есть ли несохранённые правки, которые ждут «Обновить».
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
          <span className="font-medium text-gray-900">Фильтры</span>
          {activeCount > 0 && (
            <span className="text-xs text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
              {activeCount}
            </span>
          )}
          {dirty && (
            <span className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
              не применено
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
                label="Режим"
                placeholder="Все режимы"
                options={REGIME_OPTIONS}
                value={draft.regime ?? ''}
                onChange={(e) =>
                  set('regime', (e.target.value || undefined) as Regime | undefined)
                }
              />
              <Select
                label="Страна"
                placeholder="Все страны"
                options={countries.map((c) => ({ value: c.id, label: c.name }))}
                value={draft.country_id ?? ''}
                onChange={(e) =>
                  set('country_id', e.target.value ? Number(e.target.value) : undefined)
                }
              />
              <Select
                label="Категория"
                placeholder="Все категории"
                options={categories.map((c) => ({ value: c.id, label: c.name }))}
                value={draft.category_id ?? ''}
                onChange={(e) =>
                  set('category_id', e.target.value ? Number(e.target.value) : undefined)
                }
              />
              <Select
                label="Товар"
                placeholder="Все товары"
                options={products.map((p) => ({ value: p.id, label: p.name }))}
                value={draft.product_id ?? ''}
                onChange={(e) =>
                  set('product_id', e.target.value ? Number(e.target.value) : undefined)
                }
              />
              <div className="sm:col-span-2">
                <TnvedMultiSelect
                  label="ТН ВЭД"
                  value={draft.tnved ?? []}
                  onChange={(codes) =>
                    set('tnved', codes.length > 0 ? codes : undefined)
                  }
                />
              </div>
              <Input
                label="Дата от"
                type="date"
                value={draft.date_from ?? ''}
                onChange={(e) => set('date_from', e.target.value || undefined)}
              />
              <Input
                label="Дата до"
                type="date"
                value={draft.date_to ?? ''}
                onChange={(e) => set('date_to', e.target.value || undefined)}
              />
              <div className="sm:col-span-2 lg:col-span-4">
                <Input
                  label="Поиск"
                  type="text"
                  placeholder="Название товара или ТН ВЭД..."
                  value={draft.search ?? ''}
                  onChange={(e) => set('search', e.target.value || undefined)}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-4">
              <Button type="submit" variant="primary">
                Обновить
              </Button>
              <Button type="button" variant="secondary" onClick={reset}>
                Сбросить
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
