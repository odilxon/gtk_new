'use client';

import { FormEvent, useState } from 'react';

import { RedirectIfAuth } from '@/components/AuthGuard';
import { Alert, Button, Input } from '@/components/ui';
import { useLogin } from '@/hooks/useAuth';

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

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate({ username, password });
  };

  const errorMessage =
    login.error instanceof Error
      ? login.error.message || 'Неверный логин или пароль'
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
            Внешнеторговая статистика Узбекистана
          </p>
          <p className="text-purple-300/60 text-sm mt-4 text-center">
            Анализ импорта и экспорта
          </p>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center bg-white px-8 py-12">
        <div className="w-full max-w-md">
          <div className="text-center lg:text-left mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Вход</h1>
            <p className="text-gray-500">
              Войдите в систему для доступа к данным
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {errorMessage && <Alert>{errorMessage}</Alert>}

            <Input
              label="Логин"
              name="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Введите логин"
              autoComplete="username"
              required
            />

            <Input
              label="Пароль"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
              autoComplete="current-password"
              required
            />

            <Button
              type="submit"
              loading={login.isPending}
              className="w-full py-3.5"
            >
              {login.isPending ? 'Вход...' : 'Войти'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
