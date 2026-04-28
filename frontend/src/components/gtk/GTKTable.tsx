import { RegimeBadge } from '@/components/ui';
import type { GTKRecord } from '@/types/api';

const formatNumber = (v: number | null) =>
  v === null ? '—' : v.toLocaleString('ru-RU');

const formatPrice = (v: number | null) =>
  v === null ? '—' : `$${v.toLocaleString('ru-RU')}`;

export function GTKTable({ items }: { items: GTKRecord[] }) {
  if (items.length === 0) {
    return (
      <div className="p-12 text-center">
        <p className="text-gray-500 text-sm">Записей не найдено</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-100">
            <Th>ID</Th>
            <Th>Режим</Th>
            <Th>Страна</Th>
            <Th>Категория</Th>
            <Th>Товар</Th>
            <Th>ТН ВЭД</Th>
            <Th align="right">Вес (кг)</Th>
            <Th align="right">Цена ($)</Th>
            <Th>Дата</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm text-gray-500">#{item.id}</td>
              <td className="px-4 py-3">
                <RegimeBadge regime={item.regime} />
              </td>
              <td className="px-4 py-3 text-sm text-gray-900">{item.country_name ?? '—'}</td>
              <td className="px-4 py-3 text-sm text-gray-600">{item.category_name ?? '—'}</td>
              <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                {item.product_name ?? '—'}
              </td>
              <td className="px-4 py-3 text-sm font-mono text-gray-500">{item.tnved ?? '—'}</td>
              <td className="px-4 py-3 text-sm text-gray-600 text-right">
                {formatNumber(item.weight)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                {formatPrice(item.price_thousand)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({
  children,
  align = 'left',
}: {
  children: React.ReactNode;
  align?: 'left' | 'right';
}) {
  return (
    <th
      className={`px-4 py-3 text-${align} text-xs font-medium text-gray-500 uppercase tracking-wider`}
    >
      {children}
    </th>
  );
}
