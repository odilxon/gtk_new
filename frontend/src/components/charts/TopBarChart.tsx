'use client';

import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';

import { useTopCountries, useTopOrganizations } from '@/hooks/useCharts';
import { formatPrice } from '@/lib/format';
import type { ChartFilters, ChartRegime } from '@/types/charts';

import { ChartCard } from './ChartCard';
import { EChart } from './EChart';

interface Props {
  title: string;
  source: 'countries' | 'organizations';
  regime: ChartRegime;
  filters: ChartFilters;
}

export function TopBarChart({ title, source, regime, filters }: Props) {
  const isOrg = source === 'organizations';
  const orgQ = useTopOrganizations(filters.year, regime, {
    ...filters,
    limit: 10,
  });
  const cntQ = useTopCountries(filters.year, regime, {
    ...filters,
    limit: 10,
  });
  const q = isOrg ? orgQ : cntQ;
  const { data, isLoading, error } = q;

  const option: EChartsOption = useMemo(() => {
    if (!data) return {};
    const items = [...data.items].reverse();
    return {
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v) => formatPrice(v as number),
      },
      grid: { left: 12, right: 30, top: 10, bottom: 10, containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: (v: number) => formatPrice(v) },
      },
      yAxis: {
        type: 'category',
        data: items.map((i) => i.label),
        axisLabel: {
          width: 200,
          overflow: 'truncate',
        },
      },
      series: [
        {
          type: 'bar',
          data: items.map((i) => i.value),
          itemStyle: {
            color: regime === 'import' ? '#10b981' : '#6366f1',
            borderRadius: [0, 4, 4, 0],
          },
          label: {
            show: true,
            position: 'right',
            formatter: ({ value }) => formatPrice(value as number),
          },
        },
      ],
    };
  }, [data, regime]);

  return (
    <ChartCard title={title} loading={isLoading} error={error}>
      <EChart option={option} height={380} />
    </ChartCard>
  );
}
