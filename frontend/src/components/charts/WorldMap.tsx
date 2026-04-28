'use client';

import type { EChartsOption } from 'echarts';
import { useEffect, useMemo, useState } from 'react';

import { useWorld } from '@/hooks/useCharts';
import { formatMass, formatPrice } from '@/lib/format';
import type { ChartFilters, ChartRegime, WorldPoint } from '@/types/charts';

import { ChartCard } from './ChartCard';
import { EChart, echarts } from './EChart';

const MAP_NAME = 'world';
let mapRegistered = false;

// Маппинг ISO-2 в названия из ECharts world.json (используется ISO-3 /英文)
// world.json от ECharts использует name на английском, поэтому мы делаем двойную мапу.

interface Props {
  title: string;
  regime: ChartRegime;
  filters: ChartFilters;
}

export function WorldMap({ title, regime, filters }: Props) {
  const [mapReady, setMapReady] = useState(mapRegistered);
  const { data, isLoading, error } = useWorld(filters.year, regime, filters);

  useEffect(() => {
    if (mapRegistered) return;
    fetch('/geo/world.json')
      .then((r) => r.json())
      .then((geo) => {
        echarts.registerMap(MAP_NAME, geo);
        mapRegistered = true;
        setMapReady(true);
      });
  }, []);

  // ECharts world.json features have "name" в английском; нам нужен маппинг
  // ISO2 → English name. Чтобы не таскать огромный словарь, фронт строит
  // маппинг из самой geo-карты при первой регистрации.
  const [isoToEn, setIsoToEn] = useState<Record<string, string>>({});
  useEffect(() => {
    fetch('/geo/world.json')
      .then((r) => r.json())
      .then((geo: { features: { properties: { name: string; iso_a2?: string } }[] }) => {
        const m: Record<string, string> = {};
        for (const f of geo.features) {
          const iso = f.properties.iso_a2;
          if (iso) m[iso] = f.properties.name;
        }
        setIsoToEn(m);
      });
  }, []);

  const option: EChartsOption = useMemo(() => {
    if (!data || !mapReady || Object.keys(isoToEn).length === 0) return {};
    const items = data.items
      .map((p) => {
        const enName = isoToEn[p.iso];
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
  }, [data, mapReady, isoToEn, regime]);

  return (
    <ChartCard title={title} loading={isLoading || !mapReady} error={error}>
      <EChart option={option} height={500} />
    </ChartCard>
  );
}
