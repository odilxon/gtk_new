'use client';

import { Button, Select } from '@/components/ui';
import { useCountries } from '@/hooks/useLookups';
import { useT } from '@/i18n/I18nProvider';
import type { ChartFilters as Filters } from '@/types/charts';

import { TnvedMultiSelect } from './TnvedMultiSelect';

interface Props {
  value: Filters;
  onChange: (next: Filters) => void;
}

export function ChartFilters({ value, onChange }: Props) {
  const t = useT();
  const { data: countries = [] } = useCountries();

  const set = <K extends keyof Filters>(key: K, v: Filters[K]) =>
    onChange({ ...value, [key]: v });

  const reset = () =>
    onChange({ year: value.year });

  const activeCount = [value.country_id, value.tnved?.length]
    .filter((v) => v !== undefined && v !== 0)
    .length;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-900">
          {t('filters.title')}
          {activeCount > 0 && (
            <span className="ml-2 text-xs text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
              {activeCount}
            </span>
          )}
        </h2>
        <Button variant="secondary" onClick={reset} className="px-3 py-1.5">
          {t('common.reset')}
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Select
          label={t('filters.country')}
          placeholder={t('filters.allCountries')}
          options={countries.map((c) => ({ value: c.id, label: c.name }))}
          value={value.country_id ?? ''}
          onChange={(e) =>
            set('country_id', e.target.value ? Number(e.target.value) : undefined)
          }
        />
        <TnvedMultiSelect
          label={t('filters.tnved')}
          value={value.tnved ?? []}
          onChange={(codes) =>
            set('tnved', codes.length > 0 ? codes : undefined)
          }
        />
      </div>
    </div>
  );
}
