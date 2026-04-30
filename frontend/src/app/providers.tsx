'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';

import { I18nProvider } from '@/i18n/I18nProvider';

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <I18nProvider>{children}</I18nProvider>
    </QueryClientProvider>
  );
}
