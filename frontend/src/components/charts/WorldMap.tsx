'use client';

import type { EChartsOption } from 'echarts';
import { useEffect, useMemo, useState } from 'react';

import { useWorld } from '@/hooks/useCharts';
import { formatMass, formatPrice } from '@/lib/format';
import type { ChartFilters, ChartRegime, WorldPoint } from '@/types/charts';

import { ChartCard } from './ChartCard';
import { EChart, echarts } from './EChart';
import { ISO2_TO_WORLD_NAME } from './worldMapNames';

const MAP_NAME = 'world';
let mapRegistered = false;

interface Props {
  title: string;
  regime: ChartRegime;
  filters: ChartFilters;
}

export function WorldMap({ title, regime, filters }: Props) {
  const [mapReady, setMapReady] = useState(mapRegistered);
  const { data, isLoading, error } = useWorld(filters.year, regime, filters);

  useEffect(() => {
    if (mapRegistered) {
      setMapReady(true);
      return;
    }
    fetch('/geo/world.json')
      .then((r) => r.json())
      .then((geo) => {
        echarts.registerMap(MAP_NAME, geo);
        mapRegistered = true;
        setMapReady(true);
      });
  }, []);

  const option: EChartsOption = useMemo(() => {
    if (!data || !mapReady) return {};
    const items = data.items
      .map((p) => {
        const enName = ISO2_TO_WORLD_NAME[p.iso];
        if (!enName) return null;
        return { name: enName, value: p.value, payload: p };
      })
      .filter((x): x is { name: string; value: number; payload: WorldPoint } => x !== null);

    return {
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const p = (params as { data?: { payload?: WorldPoint } }).data?.payload;
          if (!p) return (params as { name: string }).name;
          return `<b>${p.name_uz ?? p.name}</b><br/>
            Умумий: <b>${formatPrice(p.value)} $</b> | ${formatMass(p.massa)}<br/>
            Мева-сабзавот: ${formatPrice(p.meva_value)} $ | ${formatMass(p.meva_massa)}<br/>
            Озиқ-овқат: ${formatPrice(p.oziq_value)} $ | ${formatMass(p.oziq_massa)}`;
        },
      },
      visualMap: {
        min: 1,
        max: data.max_value || 1,
        calculable: true,
        orient: 'horizontal',
        left: 'left',
        bottom: 0,
        inRange: {
          color: ['#ffffff', regime === 'import' ? '#10b981' : '#6366f1'],
        },
        formatter: (v) => formatPrice(v as number),
      },
      series: [
        {
          type: 'map',
          map: MAP_NAME,
          roam: true,
          emphasis: { label: { show: false } },
          data: items,
        },
      ],
    };
  }, [data, mapReady, regime]);

  return (
    <ChartCard title={title} loading={isLoading || !mapReady} error={error}>
      <EChart option={option} height={500} />
    </ChartCard>
  );
}
