'use client';

import { useRouter } from 'next/navigation';
import { ChangeEvent, FormEvent, useEffect, useState } from 'react';

import { Alert, Button, Spinner } from '@/components/ui';
import { useCurrentUser } from '@/hooks/useAuth';
import { useT } from '@/i18n/I18nProvider';
import { adminApi } from '@/lib/api';
import type { UploadGtkResult } from '@/types/api';

const MAX_BYTES = 100 * 1024 * 1024;

export default function UploadPage() {
  const t = useT();
  const router = useRouter();
  const { data: me, isLoading: meLoading } = useCurrentUser();
  const isAdmin = !!me && me.is_admin === 1;

  useEffect(() => {
    if (!meLoading && me && !isAdmin) router.replace('/dashboard');
  }, [meLoading, me, isAdmin, router]);

  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<'idle' | 'uploading' | 'processing' | 'done'>(
    'idle',
  );
  const [result, setResult] = useState<UploadGtkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setError(null);
    setResult(null);
    if (!f) {
      setFile(null);
      return;
    }
    if (!f.name.toLowerCase().endsWith('.xlsx')) {
      setError(t('upload.onlyXlsx'));
      setFile(null);
      return;
    }
    if (f.size > MAX_BYTES) {
      setError(t('upload.sizeLimit'));
      setFile(null);
      return;
    }
    setFile(f);
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setProgress(0);
    setPhase('uploading');
    try {
      const data = await adminApi.uploadGtk(file, (p) => {
        setProgress(p);
        if (p >= 100) setPhase('processing');
      });
      setResult(data);
      setPhase('done');
    } catch (err) {
      setPhase('idle');
      setError(err instanceof Error ? err.message : t('upload.errorTitle'));
    }
  };

  if (meLoading || !isAdmin) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  const sizeMb = file ? (file.size / (1024 * 1024)).toFixed(1) : '0';
  const busy = phase === 'uploading' || phase === 'processing';

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('upload.title')}</h1>
        <p className="text-gray-500 text-sm mt-1">{t('upload.subtitle')}</p>
      </div>

      <form
        onSubmit={onSubmit}
        className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4"
      >
        <label className="block">
          <span className="block text-xs font-medium text-gray-500 mb-1.5">
            {t('upload.pickFile')}
          </span>
          <input
            type="file"
            accept=".xlsx"
            onChange={onPick}
            disabled={busy}
            className="block w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 disabled:opacity-50"
          />
          <p className="text-xs text-gray-400 mt-1.5">{t('upload.sizeLimit')}</p>
        </label>

        {file && (
          <p className="text-sm text-gray-700">
            {t('upload.selected', { name: file.name, size: sizeMb })}
          </p>
        )}

        {error && <Alert>{error}</Alert>}

        {phase === 'uploading' && (
          <div>
            <p className="text-sm text-gray-600 mb-2">
              {t('upload.uploading', { percent: progress })}
            </p>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {phase === 'processing' && (
          <div className="flex items-center gap-3 text-sm text-gray-600">
            <Spinner className="h-4 w-4" />
            {t('upload.processing')}
          </div>
        )}

        <div className="flex justify-end">
          <Button type="submit" loading={busy} disabled={!file || busy}>
            {t('upload.submit')}
          </Button>
        </div>
      </form>

      {result && (
        <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">
            {t('upload.resultTitle')}
          </h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <Row label={t('upload.rowsTotal')} value={result.rows_total} />
            <Row
              label={t('upload.added')}
              value={result.added}
              accent="text-emerald-700"
            />
            <Row
              label={t('upload.duplicatesSkipped')}
              value={result.duplicates_skipped}
              accent="text-amber-700"
            />
            <Row
              label={t('upload.invalidSkipped')}
              value={result.invalid_skipped}
              accent={result.invalid_skipped > 0 ? 'text-red-600' : undefined}
            />
            <Row
              label={t('upload.duration')}
              value={`${(result.duration_ms / 1000).toFixed(1)} s`}
            />
          </dl>
        </div>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <>
      <dt className="text-gray-500">{label}</dt>
      <dd className={`text-gray-900 font-medium ${accent ?? ''}`}>{value}</dd>
    </>
  );
}
