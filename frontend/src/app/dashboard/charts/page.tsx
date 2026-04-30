'use client';

import { useEffect, useState } from 'react';

import { ChartFilters } from '@/components/charts/ChartFilters';
import { MonthlyChart } from '@/components/charts/MonthlyChart';
import { TopBarChart } from '@/components/charts/TopBarChart';
import { TotalsCards } from '@/components/charts/TotalsCards';
import { WorldMap } from '@/components/charts/WorldMap';
import { YearTabs } from '@/components/charts/YearTabs';
import { Spinner } from '@/components/ui';
import { useChartYears } from '@/hooks/useCharts';
import { useT } from '@/i18n/I18nProvider';
import type { ChartFilters as Filters } from '@/types/charts';

export default function ChartsPage() {
  const t = useT();
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
      <div className="text-center text-gray-500 py-12">{t('charts.noData')}</div>
    );
  }

  return (
    <div className="max-w-screen-2xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('app.title')}</h1>
          <p className="text-gray-500 text-sm mt-1">{t('charts.subtitle')}</p>
        </div>
        <YearTabs
          years={years}
          active={filters.year}
          onChange={(year) => setFilters((p) => ({ ...p, year }))}
        />
      </div>

      <ChartFilters value={filters} onChange={setFilters} />

      <TotalsCards filters={filters} />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <MonthlyChart
          title={t('charts.monthlyImport')}
          field="imports"
          filters={filters}
        />
        <MonthlyChart
          title={t('charts.monthlyExport')}
          field="exports"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <MonthlyChart
          title={t('charts.monthlyImportGrowth')}
          field="import_grow"
          filters={filters}
        />
        <MonthlyChart
          title={t('charts.monthlyExportGrowth')}
          field="export_grow"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <TopBarChart
          title={t('charts.topOrgsImport')}
          source="organizations"
          regime="import"
          filters={filters}
        />
        <TopBarChart
          title={t('charts.topOrgsExport')}
          source="organizations"
          regime="export"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <TopBarChart
          title={t('charts.topCountriesImport')}
          source="countries"
          regime="import"
          filters={filters}
        />
        <TopBarChart
          title={t('charts.topCountriesExport')}
          source="countries"
          regime="export"
          filters={filters}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <WorldMap
          title={t('charts.worldImport')}
          regime="import"
          filters={filters}
        />
        <WorldMap
          title={t('charts.worldExport')}
          regime="export"
          filters={filters}
        />
      </div>
    </div>
  );
}
