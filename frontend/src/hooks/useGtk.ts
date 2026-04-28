'use client';

import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { gtkApi } from '@/lib/api';
import type { GTKListParams } from '@/types/api';

export function useGtkList(params: GTKListParams) {
  return useQuery({
    queryKey: ['gtk', 'list', params],
    queryFn: () => gtkApi.list(params),
    placeholderData: keepPreviousData,
  });
}

export function useGtkStats() {
  return useQuery({
    queryKey: ['gtk', 'stats'],
    queryFn: () => gtkApi.stats(),
  });
}

export function useGtkRecord(id: number | null) {
  return useQuery({
    queryKey: ['gtk', 'record', id],
    queryFn: () => gtkApi.getById(id as number),
    enabled: id !== null,
  });
}
