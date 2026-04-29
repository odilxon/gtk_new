'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

import { AuthGuard } from '@/components/AuthGuard';
import { useLogout } from '@/hooks/useAuth';

const navItems = [
  { href: '/dashboard/gtk', label: 'GTK Данные' },
  { href: '/dashboard/charts', label: 'Аналитика' },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <DashboardShell>{children}</DashboardShell>
    </AuthGuard>
  );
}

function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const logout = useLogout();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-30 bg-white border-b border-gray-100">
        <div className="px-6 h-14 flex items-center justify-between gap-6">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">GTK</span>
              </div>
              <span className="font-semibold text-gray-900 hidden sm:inline">
                Dashboard
              </span>
            </Link>

            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <button
            onClick={logout}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
            <span className="hidden sm:inline">Выйти</span>
          </button>
        </div>
      </header>

      <main className="p-6">{children}</main>
    </div>
  );
}
