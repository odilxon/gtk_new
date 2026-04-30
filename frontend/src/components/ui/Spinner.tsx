'use client';

import { useT } from '@/i18n/I18nProvider';
import { cn } from '@/lib/cn';

export function Spinner({ className }: { className?: string }) {
  const t = useT();
  return (
    <svg
      className={cn('animate-spin h-5 w-5 text-indigo-600', className)}
      viewBox="0 0 24 24"
      role="status"
      aria-label={t('common.loading')}
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
