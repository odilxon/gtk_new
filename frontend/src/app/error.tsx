'use client';

import { useEffect } from 'react';

import { Alert, Button } from '@/components/ui';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Что-то пошло не так</h1>
        <Alert>{error.message || 'Неизвестная ошибка'}</Alert>
        <Button onClick={reset}>Повторить</Button>
      </div>
    </div>
  );
}
