'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { UserForm } from '@/components/users/UserForm';
import { Alert, Button, Modal, Spinner } from '@/components/ui';
import { useCurrentUser } from '@/hooks/useAuth';
import {
  useCreateUser,
  useDeleteUser,
  useUpdateUser,
  useUsersList,
} from '@/hooks/useUsers';
import { useT } from '@/i18n/I18nProvider';
import type { UserAdmin, UserCreatePayload, UserUpdatePayload } from '@/types/api';

export default function UsersPage() {
  const t = useT();
  const router = useRouter();
  const { data: me, isLoading: meLoading } = useCurrentUser();
  const isAdmin = !!me && me.is_admin === 1;

  // не-админам сюда нельзя
  useEffect(() => {
    if (!meLoading && me && !isAdmin) {
      router.replace('/dashboard');
    }
  }, [meLoading, me, isAdmin, router]);

  const usersQ = useUsersList(isAdmin);
  const createMut = useCreateUser();
  const updateMut = useUpdateUser();
  const deleteMut = useDeleteUser();

  const [editing, setEditing] = useState<UserAdmin | null>(null);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const closeModals = () => {
    setEditing(null);
    setCreating(false);
    setFormError(null);
    createMut.reset();
    updateMut.reset();
  };

  const handleCreate = async (payload: UserCreatePayload | UserUpdatePayload) => {
    setFormError(null);
    try {
      await createMut.mutateAsync(payload as UserCreatePayload);
      closeModals();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : t('common.error'));
    }
  };

  const handleUpdate = async (payload: UserCreatePayload | UserUpdatePayload) => {
    if (!editing) return;
    setFormError(null);
    try {
      await updateMut.mutateAsync({
        id: editing.id,
        payload: payload as UserUpdatePayload,
      });
      closeModals();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : t('common.error'));
    }
  };

  const handleDelete = async (u: UserAdmin) => {
    if (!confirm(t('common.confirmDelete', { name: u.username }))) return;
    try {
      await deleteMut.mutateAsync(u.id);
    } catch (e) {
      alert(e instanceof Error ? e.message : t('common.error'));
    }
  };

  if (meLoading || !isAdmin) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('users.title')}</h1>
          <p className="text-gray-500 text-sm mt-1">{t('users.subtitle')}</p>
        </div>
        <Button onClick={() => setCreating(true)}>+ {t('users.create')}</Button>
      </div>

      {usersQ.error && (
        <div className="mb-4">
          <Alert>
            {usersQ.error instanceof Error
              ? usersQ.error.message
              : t('common.loadingError')}
          </Alert>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {usersQ.isLoading ? (
          <div className="p-12 text-center">
            <Spinner className="h-8 w-8 mx-auto" />
          </div>
        ) : !usersQ.data || usersQ.data.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-sm">
            {t('users.notFound')}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3">{t('users.username')}</th>
                  <th className="px-4 py-3">{t('users.email')}</th>
                  <th className="px-4 py-3">{t('users.fullName')}</th>
                  <th className="px-4 py-3">{t('users.isActive')}</th>
                  <th className="px-4 py-3">{t('users.isAdmin')}</th>
                  <th className="px-4 py-3">{t('users.createdAt')}</th>
                  <th className="px-4 py-3 text-right">{t('users.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {usersQ.data.map((u) => {
                  const isSelf = me?.id === u.id;
                  return (
                    <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {u.username}
                        {isSelf && (
                          <span className="ml-2 text-xs text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                            {t('users.selfWarn')}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {u.full_name ?? '—'}
                      </td>
                      <td className="px-4 py-3">
                        <Pill on={u.is_active === 1} />
                      </td>
                      <td className="px-4 py-3">
                        <Pill on={u.is_admin === 1} variant="admin" />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {u.created_at
                          ? new Date(u.created_at).toLocaleDateString()
                          : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="inline-flex items-center gap-2">
                          <Button
                            variant="secondary"
                            className="px-3 py-1.5"
                            onClick={() => setEditing(u)}
                          >
                            {t('common.edit')}
                          </Button>
                          <Button
                            variant="danger"
                            className="px-3 py-1.5"
                            onClick={() => handleDelete(u)}
                            disabled={isSelf}
                          >
                            {t('common.delete')}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal
        open={creating}
        onClose={closeModals}
        title={t('users.createTitle')}
      >
        <UserForm
          onSubmit={handleCreate}
          onCancel={closeModals}
          loading={createMut.isPending}
          errorMessage={formError}
        />
      </Modal>

      <Modal
        open={!!editing}
        onClose={closeModals}
        title={t('users.editTitle')}
      >
        {editing && (
          <UserForm
            user={editing}
            onSubmit={handleUpdate}
            onCancel={closeModals}
            loading={updateMut.isPending}
            errorMessage={formError}
          />
        )}
      </Modal>
    </div>
  );
}

function Pill({
  on,
  variant = 'active',
}: {
  on: boolean;
  variant?: 'active' | 'admin';
}) {
  if (!on) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
        —
      </span>
    );
  }
  const cls =
    variant === 'admin'
      ? 'bg-purple-100 text-purple-700'
      : 'bg-emerald-100 text-emerald-700';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}
    >
      ●
    </span>
  );
}
