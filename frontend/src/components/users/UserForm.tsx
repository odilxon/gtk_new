'use client';

import { FormEvent, useEffect, useState } from 'react';

import { Alert, Button, Input } from '@/components/ui';
import { useT } from '@/i18n/I18nProvider';
import type { UserAdmin, UserCreatePayload, UserUpdatePayload } from '@/types/api';

interface Props {
  user?: UserAdmin;
  onSubmit: (
    payload: UserCreatePayload | UserUpdatePayload,
  ) => Promise<unknown>;
  onCancel: () => void;
  loading?: boolean;
  errorMessage?: string | null;
}

export function UserForm({
  user,
  onSubmit,
  onCancel,
  loading,
  errorMessage,
}: Props) {
  const t = useT();
  const isEdit = !!user;

  const [username, setUsername] = useState(user?.username ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [password, setPassword] = useState('');
  const [isActive, setIsActive] = useState(user ? user.is_active === 1 : true);
  const [isAdmin, setIsAdmin] = useState(user ? user.is_admin === 1 : false);

  useEffect(() => {
    setUsername(user?.username ?? '');
    setEmail(user?.email ?? '');
    setFullName(user?.full_name ?? '');
    setPassword('');
    setIsActive(user ? user.is_active === 1 : true);
    setIsAdmin(user ? user.is_admin === 1 : false);
  }, [user]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (isEdit) {
      const payload: UserUpdatePayload = {
        email,
        full_name: fullName || null,
        is_active: isActive,
        is_admin: isAdmin,
      };
      if (password) payload.password = password;
      await onSubmit(payload);
    } else {
      const payload: UserCreatePayload = {
        username,
        email,
        password,
        full_name: fullName || null,
        is_active: isActive,
        is_admin: isAdmin,
      };
      await onSubmit(payload);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errorMessage && <Alert>{errorMessage}</Alert>}

      <Input
        label={t('users.username')}
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
        disabled={isEdit}
        autoComplete="username"
      />

      <Input
        label={t('users.email')}
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        autoComplete="email"
      />

      <Input
        label={t('users.fullName')}
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        autoComplete="name"
      />

      <div>
        <Input
          label={t('users.password')}
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required={!isEdit}
          autoComplete="new-password"
        />
        {isEdit && (
          <p className="text-xs text-gray-400 mt-1">{t('users.passwordHint')}</p>
        )}
      </div>

      <div className="flex items-center gap-6 pt-1">
        <label className="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          {t('users.isActive')}
        </label>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input
            type="checkbox"
            checked={isAdmin}
            onChange={(e) => setIsAdmin(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          {t('users.isAdmin')}
        </label>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t('common.cancel')}
        </Button>
        <Button type="submit" loading={loading}>
          {loading ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </form>
  );
}
