'use client';

import { ReactNode } from 'react';

import { Spinner } from '@/components/ui';
import { useT } from '@/i18n/I18nProvider';

interface Props {
  title: string;
  children: ReactNode;
  toolbar?: ReactNode;
  loading?: boolean;
  error?: unknown;
}

export function ChartCard({ title, children, toolbar, loading, error }: Props) {
  const t = useT();
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        {toolbar && <div className="flex items-center gap-1">{toolbar}</div>}
      </div>
      <div className="p-4 relative min-h-[260px]">
        {loading && (
          <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10">
            <Spinner className="h-6 w-6" />
          </div>
        )}
        {error ? (
          <div className="text-sm text-red-600 py-8 text-center">
            {error instanceof Error ? error.message : t('common.loadingError')}
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
