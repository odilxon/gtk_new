'use client';

import { useQuery } from '@tanstack/react-query';

import { chartsApi } from '@/lib/api';
import type { ChartFilters, ChartGroup, ChartRegime } from '@/types/charts';

export function useChartYears() {
  return useQuery({
    queryKey: ['charts', 'years'],
    queryFn: () => chartsApi.years(),
    staleTime: 30 * 60_000,
  });
}

export function useMonthly(filters: ChartFilters) {
  return useQuery({
    queryKey: ['charts', 'monthly', filters],
    queryFn: () => chartsApi.monthly(filters),
  });
}

export function useGroupSummary(
  year: number | undefined,
  group: ChartGroup,
  filters: Pick<ChartFilters, 'region_id' | 'country_id'> = {},
) {
  return useQuery({
    queryKey: ['charts', 'group-summary', year, group, filters],
    queryFn: () => chartsApi.groupSummary(year as number, group, filters),
    enabled: year !== undefined,
  });
}

export function useGroupBreakdown(
  year: number | undefined,
  group: ChartGroup,
  type: 'import' | 'export' | 'all' = 'all',
  filters: Pick<ChartFilters, 'region_id' | 'country_id'> = {},
) {
  return useQuery({
    queryKey: ['charts', 'group-breakdown', year, group, type, filters],
    queryFn: () => chartsApi.groupBreakdown(year as number, group, type, filters),
    enabled: year !== undefined,
  });
}

export function useTopOrganizations(
  year: number | undefined,
  regime: ChartRegime,
  filters: ChartFilters & { limit?: number } = {},
) {
  return useQuery({
    queryKey: ['charts', 'top-org', year, regime, filters],
    queryFn: () =>
      chartsApi.topOrganizations(year as number, regime, filters),
    enabled: year !== undefined,
  });
}

export function useTopCountries(
  year: number | undefined,
  regime: ChartRegime,
  filters: ChartFilters & { limit?: number } = {},
) {
  return useQuery({
    queryKey: ['charts', 'top-countries', year, regime, filters],
    queryFn: () => chartsApi.topCountries(year as number, regime, filters),
    enabled: year !== undefined,
  });
}

export function useRegions(
  year: number | undefined,
  regime: ChartRegime,
  filters: ChartFilters = {},
) {
  return useQuery({
    queryKey: ['charts', 'regions', year, regime, filters],
    queryFn: () => chartsApi.regions(year as number, regime, filters),
    enabled: year !== undefined,
  });
}

export function useWorld(
  year: number | undefined,
  regime: ChartRegime,
  filters: ChartFilters = {},
) {
  return useQuery({
    queryKey: ['charts', 'world', year, regime, filters],
    queryFn: () => chartsApi.world(year as number, regime, filters),
    enabled: year !== undefined,
  });
}
