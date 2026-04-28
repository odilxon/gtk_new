'use client';

import { useEffect, useState, ChangeEvent } from 'react';
import { useRouter } from 'next/navigation';
import { gtkApi } from '@/lib/api';

interface GTKRecord {
  id: number;
  regime: string;
  country_id: number;
  country_name: string;
  address_uz: string | null;
  address_foreign: string | null;
  region_id: number | null;
  region_name: string | null;
  company_uzb_id: number | null;
  company_uzb_name: string | null;
  company_foreign_id: number | null;
  company_foreign_name: string | null;
  product_id: number;
  product_name: string;
  category_id: number | null;
  category_name: string;
  tnved: string;
  unit: string | null;
  weight: number | null;
  quantity: number | null;
  price_thousand: number | null;
  date: string;
}

interface FilterParams {
  page: number;
  page_size: number;
  regime?: string;
  country_id?: number;
  region_id?: number;
  category_id?: number;
  product_id?: number;
  company_uzb_id?: number;
  company_foreign_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export default function GTKPage() {
  const router = useRouter();
  const [data, setData] = useState<{ items: GTKRecord[]; total: number; page: number; page_size: number; total_pages: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(true);

  const [filters, setFilters] = useState<FilterParams>({
    page: 1,
    page_size: 20,
  });

  const [countries, setCountries] = useState<{ id: number; name: string }[]>([]);
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [products, setProducts] = useState<{ id: number; name: string }[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
    loadFilters();
    loadData();
  }, []);

  const loadFilters = async () => {
    try {
      const [c, cat, p] = await Promise.all([
        gtkApi.getCountries(),
        gtkApi.getCategories(),
        gtkApi.getProducts(),
      ]);
      setCountries(c);
      setCategories(cat);
      setProducts(p);
    } catch (err) {
      console.error('Error loading filters:', err);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await gtkApi.getList(filters);
      setData(result);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof FilterParams, value: string | number | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  const handleSearch = (e: ChangeEvent<HTMLInputElement>) => {
    handleFilterChange('search', e.target.value || undefined);
  };

  const handleApply = () => {
    loadData();
  };

  const handleReset = () => {
    setFilters({ page: 1, page_size: 20 });
    setTimeout(loadData, 0);
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
    loadData();
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">GTK Данные</h1>
        <p className="text-gray-500 text-sm mt-1">Внешнеторговая деятельность Узбекистана</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
        <button
          onClick={() => setFiltersOpen(!filtersOpen)}
          className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <span className="font-medium text-gray-900">Фильтры</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              {Object.values(filters).filter(v => v !== undefined && v !== '' && v !== 1 && v !== 20).length}
            </span>
          </div>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${filtersOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {filtersOpen && (
          <div className="px-5 pb-5 border-t border-gray-100">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Режим</label>
                <select
                  value={filters.regime || ''}
                  onChange={(e) => handleFilterChange('regime', e.target.value || undefined)}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                >
                  <option value="">Все режимы</option>
                  <option value="ИМ">ИМ (Импорт)</option>
                  <option value="ЭК">ЭК (Экспорт)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Страна</label>
                <select
                  value={filters.country_id || ''}
                  onChange={(e) => handleFilterChange('country_id', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                >
                  <option value="">Все страны</option>
                  {countries.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Категория</label>
                <select
                  value={filters.category_id || ''}
                  onChange={(e) => handleFilterChange('category_id', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                >
                  <option value="">Все категории</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Товар</label>
                <select
                  value={filters.product_id || ''}
                  onChange={(e) => handleFilterChange('product_id', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                >
                  <option value="">Все товары</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Дата от</label>
                <input
                  type="date"
                  value={filters.date_from || ''}
                  onChange={(e) => handleFilterChange('date_from', e.target.value || undefined)}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Дата до</label>
                <input
                  type="date"
                  value={filters.date_to || ''}
                  onChange={(e) => handleFilterChange('date_to', e.target.value || undefined)}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                />
              </div>

              <div className="sm:col-span-2 lg:col-span-2">
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Поиск</label>
                <input
                  type="text"
                  placeholder="Название товара или ТН ВЭД..."
                  value={filters.search || ''}
                  onChange={handleSearch}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 placeholder-gray-400 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-4">
              <button
                onClick={handleApply}
                className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-medium text-sm hover:bg-indigo-700 transition-colors"
              >
                Применить
              </button>
              <button
                onClick={handleReset}
                className="px-5 py-2.5 bg-gray-100 text-gray-600 rounded-lg font-medium text-sm hover:bg-gray-200 transition-colors"
              >
                Сброс
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <svg className="animate-spin h-8 w-8 text-indigo-600 mx-auto" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-gray-500 text-sm mt-3">Загрузка данных...</p>
          </div>
        ) : data ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Режим</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Страна</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Категория</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Товар</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ТН ВЭД</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Вес (кг)</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Цена ($)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Дата</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {data.items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-sm text-gray-500">#{item.id}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          item.regime === 'ИМ' 
                            ? 'bg-emerald-100 text-emerald-700' 
                            : 'bg-indigo-100 text-indigo-700'
                        }`}>
                          {item.regime}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{item.country_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{item.category_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">{item.product_name}</td>
                      <td className="px-4 py-3 text-sm font-mono text-gray-500">{item.tnved}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 text-right">
                        {item.weight ? item.weight.toLocaleString() : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                        {item.price_thousand ? `$${item.price_thousand.toLocaleString()}` : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">{item.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="text-sm text-gray-500">
                Показано <span className="font-medium">{((data.page - 1) * data.page_size) + 1}</span> —{' '}
                <span className="font-medium">{Math.min(data.page * data.page_size, data.total)}</span> из{' '}
                <span className="font-medium">{data.total.toLocaleString()}</span> записей
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(data.page - 1)}
                  disabled={data.page <= 1}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  ← Назад
                </button>
                <span className="px-3 py-1.5 text-sm text-gray-600">
                  Страница <span className="font-medium">{data.page}</span> из{' '}
                  <span className="font-medium">{data.total_pages}</span>
                </span>
                <button
                  onClick={() => handlePageChange(data.page + 1)}
                  disabled={data.page >= data.total_pages}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Вперёд →
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="p-12 text-center">
            <svg className="w-12 h-12 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-500 text-sm mt-3">Нет данных</p>
          </div>
        )}
      </div>
    </div>
  );
}