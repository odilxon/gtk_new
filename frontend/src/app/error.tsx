'use client';

import { useEffect } from 'react';

import { Alert, Button } from '@/components/ui';
import { useT } from '@/i18n/I18nProvider';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useT();
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">
          {t('errorPage.title')}
        </h1>
        <Alert>{error.message || t('errorPage.unknown')}</Alert>
        <Button onClick={reset}>{t('errorPage.retry')}</Button>
      </div>
    </div>
  );
}
