export function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  let n = Number(value);
  let suffix = '';
  if (n >= 1000) {
    n = n / 1000;
    suffix = ' минг';
  }
  if (n >= 1000) {
    n = n / 1000;
    suffix = ' млн';
  }
  if (n >= 1000) {
    n = n / 1000;
    suffix = ' млрд';
  }
  return n.toLocaleString('ru-RU', { maximumFractionDigits: 2 }) + suffix;
}

export function formatMass(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  let n = Number(value);
  let suffix = ' кг';
  if (n >= 1000) {
    n = n / 1000;
    suffix = ' т';
  }
  if (n >= 1000) {
    n = n / 1000;
    suffix = ' минг т';
  }
  return n.toLocaleString('ru-RU', { maximumFractionDigits: 2 }) + suffix;
}

export function formatThousand(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return Number(value).toLocaleString('ru-RU', { maximumFractionDigits: 2 });
}
