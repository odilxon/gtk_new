'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';

import { authApi, tokenStorage } from '@/lib/api';
import type { User } from '@/types/api';

export function useCurrentUser() {
  return useQuery<User | null>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      if (!tokenStorage.get()) return null;
      try {
        return await authApi.me();
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60_000,
  });
}

export function useLogin() {
  const router = useRouter();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.login(username, password),
    onSuccess: (data) => {
      qc.setQueryData(['auth', 'me'], data.user);
      router.push('/dashboard');
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const qc = useQueryClient();
  return () => {
    authApi.logout();
    qc.clear();
    router.push('/login');
  };
}
