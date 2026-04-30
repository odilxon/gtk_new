'use client';

import { FormEvent, useState } from 'react';

import { RedirectIfAuth } from '@/components/AuthGuard';
import { Alert, Button, Input, LanguageSwitcher } from '@/components/ui';
import { useLogin } from '@/hooks/useAuth';
import { useT } from '@/i18n/I18nProvider';

export default function LoginPage() {
  return (
    <RedirectIfAuth>
      <LoginForm />
    </RedirectIfAuth>
  );
}

function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const login = useLogin();
  const t = useT();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate({ username, password });
  };

  const errorMessage =
    login.error instanceof Error
      ? login.error.message || t('auth.invalid')
      : null;

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-center items-center w-full text-white px-12">
          <h2 className="text-5xl font-bold mb-4 text-center">GTK</h2>
          <p className="text-xl text-purple-200 text-center max-w-md">
            {t('app.title')}
          </p>
          <p className="text-purple-300/60 text-sm mt-4 text-center">
            {t('app.tagline')}
          </p>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-8 py-12 relative">
        <div className="absolute top-6 right-6">
          <LanguageSwitcher />
        </div>
        <div className="w-full max-w-md">
          <div className="text-center lg:text-left mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {t('auth.title')}
            </h1>
            <p className="text-gray-500">{t('auth.subtitle')}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {errorMessage && <Alert>{errorMessage}</Alert>}

            <Input
              label={t('auth.login')}
              name="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t('auth.loginPlaceholder')}
              autoComplete="username"
              required
            />

            <Input
              label={t('auth.password')}
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.passwordPlaceholder')}
              autoComplete="current-password"
              required
            />

            <Button
              type="submit"
              loading={login.isPending}
              className="w-full py-3.5"
            >
              {login.isPending ? t('auth.submitting') : t('auth.submit')}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
