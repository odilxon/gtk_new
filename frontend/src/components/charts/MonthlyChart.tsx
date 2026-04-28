'use client';

import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';

import { useMonthly } from '@/hooks/useCharts';
import { formatPrice } from '@/lib/format';
import type { ChartFilters } from '@/types/charts';

import { ChartCard } from './ChartCard';
import { EChart } from './EChart';

const PALETTE = ['#892CDC', '#32E0C4', '#222831', '#50D890', '#30475E', '#F05454'];

interface Props {
  title: string;
  field: 'imports' | 'exports' | 'import_grow' | 'export_grow';
  filters: ChartFilters;
}

export function MonthlyChart({ title, field, filters }: Props) {
  const { data, isLoading, error } = useMonthly(filters);

  const option: EChartsOption = useMemo(() => {
    if (!data) return {};
    const series = Object.entries(data[field]).map(([year, values], i) => ({
      name: `${year}`,
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: values,
      color: PALETTE[i % PALETTE.length],
    }));
    return {
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v) => (v == null ? '—' : formatPrice(v as number)),
      },
      legend: { top: 0 },
      grid: { top: 40, left: 50, right: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        data: data.months,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (val: number) => formatPrice(val),
        },
      },
      series,
    };
  }, [data, field]);

  return (
    <ChartCard title={title} loading={isLoading} error={error}>
      <EChart option={option} height={380} />
    </ChartCard>
  );
}
