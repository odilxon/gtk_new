'use client';

import type { EChartsOption } from 'echarts';
import { useEffect, useMemo, useState } from 'react';

import { useRegions } from '@/hooks/useCharts';
import { formatMass, formatPrice } from '@/lib/format';
import type { ChartFilters, ChartRegime } from '@/types/charts';

import { ChartCard } from './ChartCard';
import { EChart, echarts } from './EChart';

const MAP_NAME = 'uzbekistan';

let mapRegistered = false;

interface Props {
  title: string;
  regime: ChartRegime;
  filters: ChartFilters;
}

export function UzbekistanMap({ title, regime, filters }: Props) {
  const [mapReady, setMapReady] = useState(mapRegistered);
  const { data, isLoading, error } = useRegions(filters.year, regime, filters);

  useEffect(() => {
    if (mapRegistered) return;
    fetch('/geo/uzbekistan.json')
      .then((r) => r.json())
      .then((geo) => {
        echarts.registerMap(MAP_NAME, geo);
        mapRegistered = true;
        setMapReady(true);
      });
  }, []);

  const option: EChartsOption = useMemo(() => {
    if (!data || !mapReady) return {};
    const items = data.items.map((p) => ({
      name: p.name,
      value: p.value,
      payload: p,
    }));
    return {
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const p = (params as { data?: { payload?: typeof data.items[number] } }).data?.payload;
          if (!p) return (params as { name: string }).name;
          return `<b>${p.name}</b><br/>
            Умумий: <b>${formatPrice(p.value)} $</b> | ${formatMass(p.massa)}<br/>
            Мева-сабзавот: ${formatPrice(p.meva_total)} $ | ${formatMass(p.meva_massa)}<br/>
            Озиқ-овқат: ${formatPrice(p.oziq_total)} $ | ${formatMass(p.oziq_massa)}`;
        },
      },
      visualMap: {
        min: 0,
        max: data.max_value || 1,
        calculable: true,
        orient: 'horizontal',
        left: 'left',
        bottom: 0,
        inRange: {
          color:
            regime === 'import'
              ? ['#ecfdf5', '#10b981', '#065f46']
              : ['#eef2ff', '#6366f1', '#312e81'],
        },
        formatter: (v) => formatPrice(v as number),
      },
      series: [
        {
          name: 'Вилоят',
          type: 'map',
          map: MAP_NAME,
          roam: false,
          label: { show: true, fontSize: 9 },
          data: items,
          emphasis: {
            label: { show: true, fontWeight: 'bold' },
          },
        },
      ],
    };
  }, [data, mapReady, regime]);

  return (
    <ChartCard title={title} loading={isLoading || !mapReady} error={error}>
      <EChart option={option} height={420} />
    </ChartCard>
  );
}
