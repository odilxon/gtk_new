'use client';

import { Button } from './Button';

interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
}: PaginationProps) {
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
      <div className="text-sm text-gray-500">
        Показано <span className="font-medium">{from}</span> —{' '}
        <span className="font-medium">{to}</span> из{' '}
        <span className="font-medium">{total.toLocaleString()}</span> записей
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5"
        >
          ← Назад
        </Button>
        <span className="px-3 py-1.5 text-sm text-gray-600">
          Страница <span className="font-medium">{page}</span> из{' '}
          <span className="font-medium">{Math.max(totalPages, 1)}</span>
        </span>
        <Button
          variant="secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1.5"
        >
          Вперёд →
        </Button>
      </div>
    </div>
  );
}
