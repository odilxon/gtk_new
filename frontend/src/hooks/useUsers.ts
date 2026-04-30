'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { usersApi } from '@/lib/api';
import type { UserCreatePayload, UserUpdatePayload } from '@/types/api';

const KEY = ['users', 'list'] as const;

export function useUsersList(enabled = true) {
  return useQuery({
    queryKey: KEY,
    queryFn: () => usersApi.list(),
    enabled,
    staleTime: 60_000,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserCreatePayload) => usersApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UserUpdatePayload }) =>
      usersApi.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => usersApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
