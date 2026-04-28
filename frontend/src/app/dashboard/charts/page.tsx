'use client';

import { useEffect, useState } from 'react';

import { ChartFilters } from '@/components/charts/ChartFilters';
import { GroupCard } from '@/components/charts/GroupCard';
import { MonthlyChart } from '@/components/charts/MonthlyChart';
import { TopBarChart } from '@/components/charts/TopBarChart';
import { UzbekistanMap } from '@/components/charts/UzbekistanMap';
import { WorldMap } from '@/components/charts/WorldMap';
import { YearTabs } from '@/components/charts/YearTabs';
import { Spinner } from '@/components/ui';
import { useChartYears } from '@/hooks/useCharts';
import type { ChartFilters as Filters } from '@/types/charts';

export default function ChartsPage() {
  const { data: years = [], isLoading: yearsLoading } = useChartYears();
  const [filters, setFilters] = useState<Filters>({});

  useEffect(() => {
    if (filters.year === undefined && years.length > 0) {
      setFilters((p) => ({ ...p, year: years[0] }));
    }
  }, [years, filters.year]);

  if (yearsLoading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (years.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        Нет данных в БД. Загрузите данные через ETL.
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Қишлоқ хўжалиги маҳсулотлари ташқи савдо айланмаси
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Аналитика по импорту и экспорту
          </p>
        </div>
        <YearTabs
          years={years}
          active={filters.year}
          onChange={(year) => setFilters((p) => ({ ...p, year }))}
        />
      </div>

      <ChartFilters value={filters} onChange={setFilters} />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <GroupCard title="Озиқ-овқат" group="oziq" filters={filters} />
        <GroupCard title="Мева-сабзавот" group="meva" filters={filters} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <MonthlyChart
          title="Йиллар бўйича импорт графиги"
          field="imports"
          filters={filters}
        />
        <MonthlyChart
          title="Йиллар бўйича экспорт графиги"
          field="exports"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <MonthlyChart
          title="Йиллар бўйича импорт ўсиши"
          field="import_grow"
          filters={filters}
        />
        <MonthlyChart
          title="Йиллар бўйича экспорт ўсиши"
          field="export_grow"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <TopBarChart
          title="Импорт хажми юқори ташкилотлар"
          source="organizations"
          regime="import"
          filters={filters}
        />
        <TopBarChart
          title="Экспорт хажми юқори ташкилотлар"
          source="organizations"
          regime="export"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <UzbekistanMap
          title="Импорт по областям"
          regime="import"
          filters={filters}
        />
        <UzbekistanMap
          title="Экспорт по областям"
          regime="export"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <TopBarChart
          title="Импорт хажми юқори давлатлар"
          source="countries"
          regime="import"
          filters={filters}
        />
        <TopBarChart
          title="Экспорт хажми юқори давлатлар"
          source="countries"
          regime="export"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <WorldMap
          title="Импорт по странам мира"
          regime="import"
          filters={filters}
        />
        <WorldMap
          title="Экспорт по странам мира"
          regime="export"
          filters={filters}
        />
      </div>
    </div>
  );
}
