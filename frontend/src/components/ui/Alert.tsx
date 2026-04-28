import { ReactNode } from 'react';

import { cn } from '@/lib/cn';

type Variant = 'error' | 'info';

const styles: Record<Variant, string> = {
  error: 'bg-red-50 text-red-600 border-red-100',
  info: 'bg-blue-50 text-blue-600 border-blue-100',
};

export function Alert({
  children,
  variant = 'error',
}: {
  children: ReactNode;
  variant?: Variant;
}) {
  return (
    <div
      role="alert"
      className={cn('p-4 rounded-lg text-sm border', styles[variant])}
    >
      {children}
    </div>
  );
}
