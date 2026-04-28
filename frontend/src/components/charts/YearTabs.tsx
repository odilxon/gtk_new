'use client';

import { cn } from '@/lib/cn';

interface Props {
  years: number[];
  active: number | undefined;
  onChange: (year: number) => void;
  size?: 'sm' | 'md';
}

export function YearTabs({ years, active, onChange, size = 'md' }: Props) {
  return (
    <div className="flex flex-wrap gap-1">
      {years.map((y) => {
        const isActive = y === active;
        return (
          <button
            key={y}
            onClick={() => onChange(y)}
            className={cn(
              'rounded-lg font-medium transition-colors',
              size === 'sm'
                ? 'px-2.5 py-1 text-xs'
                : 'px-3 py-1.5 text-sm',
              isActive
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
            )}
          >
            {y}
          </button>
        );
      })}
    </div>
  );
}
