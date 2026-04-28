'use client';

import { useQuery } from '@tanstack/react-query';

import { lookupsApi } from '@/lib/api';

const LONG_STALE = 30 * 60_000;

export function useCountries() {
  return useQuery({
    queryKey: ['lookups', 'countries'],
    queryFn: () => lookupsApi.countries(),
    staleTime: LONG_STALE,
  });
}

export function useRegions() {
  return useQuery({
    queryKey: ['lookups', 'regions'],
    queryFn: () => lookupsApi.regions(),
    staleTime: LONG_STALE,
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ['lookups', 'categories'],
    queryFn: () => lookupsApi.categories(),
    staleTime: LONG_STALE,
  });
}

export function useProducts(categoryId?: number, search?: string) {
  return useQuery({
    queryKey: ['lookups', 'products', categoryId, search],
    queryFn: () => lookupsApi.products(categoryId, search),
    staleTime: LONG_STALE,
  });
}

export function useCompaniesUzb() {
  return useQuery({
    queryKey: ['lookups', 'companies-uzb'],
    queryFn: () => lookupsApi.companiesUzb(),
    staleTime: LONG_STALE,
  });
}

export function useCompaniesForeign() {
  return useQuery({
    queryKey: ['lookups', 'companies-foreign'],
    queryFn: () => lookupsApi.companiesForeign(),
    staleTime: LONG_STALE,
  });
}
