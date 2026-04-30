'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import { useTnvedSearch } from '@/hooks/useLookups';
import { useT } from '@/i18n/I18nProvider';
import { cn } from '@/lib/cn';

interface Props {
  label?: string;
  value: string[];
  onChange: (codes: string[]) => void;
  placeholder?: string;
  minChars?: number;
  debounceMs?: number;
}

export function TnvedMultiSelect({
  label,
  value,
  onChange,
  placeholder,
  minChars = 3,
  debounceMs = 250,
}: Props) {
  const t = useT();
  const ph = placeholder ?? t('tnved.placeholder');
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), debounceMs);
    return () => clearTimeout(t);
  }, [query, debounceMs]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  // wildcard: пользователь явно поставил `*` в конце — берём префикс без `*`
  // и подгружаем больше совпадений, чтобы можно было разом добавить все.
  const trimmedDebounced = debounced.trim();
  const isWildcard = trimmedDebounced.endsWith('*');
  const searchTerm = isWildcard ? trimmedDebounced.slice(0, -1) : trimmedDebounced;
  const enabled = open && searchTerm.length >= minChars;
  const { data, isFetching } = useTnvedSearch(
    searchTerm,
    enabled,
    isWildcard ? 1000 : 30,
  );

  const selected = useMemo(() => new Set(value), [value]);
  const filteredResults = useMemo(
    () => (data ?? []).filter((it) => !selected.has(it.tnved)),
    [data, selected],
  );

  const add = (code: string) => {
    if (!selected.has(code)) onChange([...value, code]);
    setQuery('');
    setDebounced('');
  };
  const addAll = () => {
    const next = [...value];
    const seen = new Set(value);
    for (const it of filteredResults) {
      if (!seen.has(it.tnved)) {
        next.push(it.tnved);
        seen.add(it.tnved);
      }
    }
    onChange(next);
    setQuery('');
    setDebounced('');
  };
  const remove = (code: string) => onChange(value.filter((c) => c !== code));
  const clearAll = () => onChange([]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && isWildcard && filteredResults.length > 0) {
      e.preventDefault();
      addAll();
    }
  };

  return (
    <div ref={wrapRef} className="relative">
      {label && (
        <label className="block text-xs font-medium text-gray-500 mb-1.5">
          {label}
        </label>
      )}

      <div
        className={cn(
          'min-h-[42px] w-full rounded-lg border border-gray-200 bg-white px-2 py-1.5 flex flex-wrap items-center gap-1.5 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100 transition-all',
        )}
        onClick={() => setOpen(true)}
      >
        {value.map((code) => (
          <span
            key={code}
            className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 text-xs font-medium px-2 py-1 rounded-md"
          >
            {code}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                remove(code);
              }}
              className="hover:text-indigo-900"
              aria-label={t('tnved.removeAria', { code })}
            >
              ×
            </button>
          </span>
        ))}

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder={value.length === 0 ? ph : ''}
          className="flex-1 min-w-[120px] outline-none text-sm py-1 px-1 bg-transparent"
        />

        {value.length > 0 && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              clearAll();
            }}
            className="text-xs text-gray-400 hover:text-gray-600 px-1"
            title={t('common.clearTitle')}
          >
            {t('common.clear')}
          </button>
        )}
      </div>

      {open && searchTerm.length >= minChars && (
        <div className="absolute z-20 mt-1 w-full max-h-72 overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg">
          {isFetching && (
            <div className="px-3 py-2 text-xs text-gray-400">
              {t('tnved.searching')}
            </div>
          )}
          {!isFetching && isWildcard && filteredResults.length > 0 && (
            <button
              type="button"
              onClick={addAll}
              className="w-full text-left px-3 py-2 text-sm bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium border-b border-indigo-100"
            >
              {t('tnved.addAll', {
                prefix: searchTerm,
                count: filteredResults.length,
              })}
            </button>
          )}
          {!isFetching && filteredResults.length === 0 && (
            <div className="px-3 py-2 text-xs text-gray-400">
              {t('tnved.notFound')}
            </div>
          )}
          {!isFetching &&
            filteredResults.map((it) => (
              <button
                key={it.tnved}
                type="button"
                onClick={() => add(it.tnved)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-indigo-50 flex items-baseline gap-2"
              >
                <span className="font-mono text-indigo-700">{it.tnved}</span>
                <span className="text-gray-600 truncate">{it.name}</span>
              </button>
            ))}
        </div>
      )}

      {open && trimmedDebounced.length > 0 && searchTerm.length < minChars && (
        <div className="absolute z-20 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg px-3 py-2 text-xs text-gray-400">
          {t('tnved.moreChars', { n: minChars - searchTerm.length })}
          {isWildcard ? t('tnved.beforeAsterisk') : ''}
        </div>
      )}
    </div>
  );
}
