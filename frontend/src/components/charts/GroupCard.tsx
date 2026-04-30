'use client';

import { useGroupBreakdown, useGroupSummary } from '@/hooks/useCharts';
import { formatMass, formatPrice, formatThousand } from '@/lib/format';
import type { ChartFilters, ChartGroup } from '@/types/charts';

import { ChartCard } from './ChartCard';

interface Props {
  title: string;
  group: ChartGroup;
  filters: ChartFilters;
}

export function GroupCard({ title, group, filters }: Props) {
  const year = filters.year;
  const innerFilters = {
    region_id: filters.region_id,
    country_id: filters.country_id,
    tnved: filters.tnved,
  };
  const { data: summary, isLoading, error } = useGroupSummary(year, group, innerFilters);
  const { data: breakdown } = useGroupBreakdown(year, group, 'all', innerFilters);

  return (
    <ChartCard title={title} loading={isLoading} error={error}>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <Stat
          label="Умумий"
          color="bg-purple-500"
          total={summary?.total.total}
          massa={summary?.total.massa}
        />
        <Stat
          label="Импорт"
          color="bg-teal-500"
          total={summary?.import_.total}
          massa={summary?.import_.massa}
        />
        <Stat
          label="Экспорт"
          color="bg-sky-500"
          total={summary?.export.total}
          massa={summary?.export.massa}
        />
      </div>

      {breakdown && breakdown.rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                <th className="py-2 pr-2 font-medium">Тоифа</th>
                <th className="py-2 pr-2 font-medium text-right">Ҳажми</th>
                <th className="py-2 pr-2 font-medium text-right">Жами</th>
                <th className="py-2 font-medium text-right">Ўртача</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {breakdown.rows.slice(0, 10).map((r) => (
                <tr key={r.name}>
                  <td className="py-2 pr-2 text-gray-700">{r.name}</td>
                  <td className="py-2 pr-2 text-gray-600 text-right">
                    {formatMass(r.massa)}
                  </td>
                  <td className="py-2 pr-2 text-gray-900 text-right font-medium">
                    {formatPrice(r.total)} $
                  </td>
                  <td className="py-2 text-gray-500 text-right">
                    {formatThousand(r.avg)} кг/$
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ChartCard>
  );
}

function Stat({
  label,
  color,
  total,
  massa,
}: {
  label: string;
  color: string;
  total: number | undefined;
  massa: number | undefined;
}) {
  return (
    <div className="rounded-lg p-3 bg-gray-50">
      <div className={`w-2 h-2 rounded-full ${color} mb-2`} />
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold text-gray-900 mt-1">
        {formatPrice(total)} $
      </p>
      <p className="text-xs text-gray-600">{formatMass(massa)}</p>
    </div>
  );
}
