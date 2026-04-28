'use client';

import { useState } from 'react';

import { Button, Input, Select } from '@/components/ui';
import {
  useCategories,
  useCountries,
  useProducts,
} from '@/hooks/useLookups';
import type { GTKListParams, Regime } from '@/types/api';

interface Props {
  value: GTKListParams;
  onChange: (next: GTKListParams) => void;
}

const REGIME_OPTIONS = [
  { value: 'ИМ', label: 'ИМ (Импорт)' },
  { value: 'ЭК', label: 'ЭК (Экспорт)' },
];

export function GTKFilters({ value, onChange }: Props) {
  const [open, setOpen] = useState(true);
  const { data: countries = [] } = useCountries();
  const { data: categories = [] } = useCategories();
  const { data: products = [] } = useProducts(value.category_id);

  const set = <K extends keyof GTKListParams>(key: K, v: GTKListParams[K]) =>
    onChange({ ...value, [key]: v, page: 1 });

  const reset = () => onChange({ page: 1, page_size: value.page_size });

  const activeCount = [
    value.regime,
    value.country_id,
    value.category_id,
    value.product_id,
    value.date_from,
    value.date_to,
    value.search,
  ].filter((v) => v !== undefined && v !== '').length;

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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            <Select
              label="Режим"
              placeholder="Все режимы"
              options={REGIME_OPTIONS}
              value={value.regime ?? ''}
              onChange={(e) =>
                set('regime', (e.target.value || undefined) as Regime | undefined)
              }
            />
            <Select
              label="Страна"
              placeholder="Все страны"
              options={countries.map((c) => ({ value: c.id, label: c.name }))}
              value={value.country_id ?? ''}
              onChange={(e) =>
                set('country_id', e.target.value ? Number(e.target.value) : undefined)
              }
            />
            <Select
              label="Категория"
              placeholder="Все категории"
              options={categories.map((c) => ({ value: c.id, label: c.name }))}
              value={value.category_id ?? ''}
              onChange={(e) =>
                set('category_id', e.target.value ? Number(e.target.value) : undefined)
              }
            />
            <Select
              label="Товар"
              placeholder="Все товары"
              options={products.map((p) => ({ value: p.id, label: p.name }))}
              value={value.product_id ?? ''}
              onChange={(e) =>
                set('product_id', e.target.value ? Number(e.target.value) : undefined)
              }
            />
            <Input
              label="Дата от"
              type="date"
              value={value.date_from ?? ''}
              onChange={(e) => set('date_from', e.target.value || undefined)}
            />
            <Input
              label="Дата до"
              type="date"
              value={value.date_to ?? ''}
              onChange={(e) => set('date_to', e.target.value || undefined)}
            />
            <div className="sm:col-span-2">
              <Input
                label="Поиск"
                type="text"
                placeholder="Название товара или ТН ВЭД..."
                value={value.search ?? ''}
                onChange={(e) => set('search', e.target.value || undefined)}
              />
            </div>
          </div>

          <div className="flex gap-3 mt-4">
            <Button variant="secondary" onClick={reset}>
              Сбросить
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
