'use client';

import { useState } from 'react';

import { GTKFilters } from '@/components/gtk/GTKFilters';
import { GTKTable } from '@/components/gtk/GTKTable';
import { Alert, Pagination, Spinner } from '@/components/ui';
import { useGtkList } from '@/hooks/useGtk';
import type { GTKListParams } from '@/types/api';

const DEFAULT_PAGE_SIZE = 20;

export default function GTKPage() {
  const [filters, setFilters] = useState<GTKListParams>({
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  });

  const { data, isLoading, isFetching, error } = useGtkList(filters);

  const handlePageChange = (page: number) =>
    setFilters((prev) => ({ ...prev, page }));

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">GTK Данные</h1>
        <p className="text-gray-500 text-sm mt-1">
          Внешнеторговая деятельность Узбекистана
        </p>
      </div>

      <GTKFilters value={filters} onChange={setFilters} />

      {error && (
        <div className="mb-4">
          <Alert>{error instanceof Error ? error.message : 'Ошибка загрузки'}</Alert>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <Spinner className="h-8 w-8 mx-auto" />
            <p className="text-gray-500 text-sm mt-3">Загрузка данных...</p>
          </div>
        ) : data ? (
          <>
            <div className={isFetching ? 'opacity-60 transition-opacity' : ''}>
              <GTKTable items={data.items} />
            </div>
            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              total={data.total}
              pageSize={data.page_size}
              onPageChange={handlePageChange}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
