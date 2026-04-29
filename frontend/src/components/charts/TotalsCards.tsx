'use client';

import { useTotals } from '@/hooks/useCharts';
import { formatMass, formatPrice } from '@/lib/format';
import type { ChartFilters } from '@/types/charts';

interface Props {
  filters: ChartFilters;
}

export function TotalsCards({ filters }: Props) {
  const { data, isLoading, error } = useTotals(filters.year, {
    tnved: filters.tnved,
    region_id: filters.region_id,
    country_id: filters.country_id,
  });

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <Card
        label="Умумий"
        color="bg-purple-500"
        total={data?.total.total}
        massa={data?.total.massa}
        loading={isLoading}
        error={error}
      />
      <Card
        label="Импорт"
        color="bg-teal-500"
        total={data?.import_.total}
        massa={data?.import_.massa}
        loading={isLoading}
        error={error}
      />
      <Card
        label="Экспорт"
        color="bg-sky-500"
        total={data?.export.total}
        massa={data?.export.massa}
        loading={isLoading}
        error={error}
      />
    </div>
  );
}

function Card({
  label,
  color,
  total,
  massa,
  loading,
  error,
}: {
  label: string;
  color: string;
  total: number | undefined;
  massa: number | undefined;
  loading: boolean;
  error: unknown;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-2.5 h-2.5 rounded-full ${color}`} />
        <p className="text-sm font-medium text-gray-500">{label}</p>
      </div>
      {error ? (
        <p className="text-sm text-red-500">Ошибка</p>
      ) : loading ? (
        <>
          <div className="h-7 w-32 bg-gray-100 rounded animate-pulse mb-2" />
          <div className="h-4 w-24 bg-gray-100 rounded animate-pulse" />
        </>
      ) : (
        <>
          <p className="text-2xl font-bold text-gray-900">
            {formatPrice(total)} <span className="text-base font-normal text-gray-500">$</span>
          </p>
          <p className="text-sm text-gray-600 mt-1">{formatMass(massa)}</p>
        </>
      )}
    </div>
  );
}
