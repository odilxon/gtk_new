'use client';

import { useRouter } from 'next/navigation';
import { ReactNode, useEffect } from 'react';

import { tokenStorage } from '@/lib/api';
import { useCurrentUser } from '@/hooks/useAuth';

import { Spinner } from './ui/Spinner';

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();

  useEffect(() => {
    if (isLoading) return;
    if (!tokenStorage.get() || !user) {
      router.replace('/login');
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return <>{children}</>;
}

export function RedirectIfAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace('/dashboard');
    }
  }, [isLoading, user, router]);

  return <>{children}</>;
}
