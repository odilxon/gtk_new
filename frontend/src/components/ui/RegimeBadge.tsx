import type { Regime } from '@/types/api';
import { cn } from '@/lib/cn';

const styles: Record<Regime, string> = {
  ИМ: 'bg-emerald-100 text-emerald-700',
  ЭК: 'bg-indigo-100 text-indigo-700',
};

export function RegimeBadge({ regime }: { regime: Regime }) {
  return (
    <span
      className={cn(
        'px-2.5 py-1 rounded-full text-xs font-medium',
        styles[regime],
      )}
    >
      {regime}
    </span>
  );
}
