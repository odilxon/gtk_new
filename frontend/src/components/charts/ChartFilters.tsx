'use client';

import { Button, Select } from '@/components/ui';
import { useCountries, useRegions } from '@/hooks/useLookups';
import type { ChartFilters as Filters } from '@/types/charts';

interface Props {
  value: Filters;
  onChange: (next: Filters) => void;
}

export function ChartFilters({ value, onChange }: Props) {
  const { data: countries = [] } = useCountries();
  const { data: regions = [] } = useRegions();

  const set = <K extends keyof Filters>(key: K, v: Filters[K]) =>
    onChange({ ...value, [key]: v });

  const reset = () =>
    onChange({ year: value.year });

  const activeCount = [value.country_id, value.region_id, value.tnved?.length]
    .filter((v) => v !== undefined && v !== 0)
    .length;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-900">
          Фильтры
          {activeCount > 0 && (
            <span className="ml-2 text-xs text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
              {activeCount}
            </span>
          )}
        </h2>
        <Button variant="secondary" onClick={reset} className="px-3 py-1.5">
          Сбросить
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
          label="Область"
          placeholder="Все области"
          options={regions.map((r) => ({ value: r.id, label: r.name }))}
          value={value.region_id ?? ''}
          onChange={(e) =>
            set('region_id', e.target.value ? Number(e.target.value) : undefined)
          }
        />
      </div>
    </div>
  );
}
