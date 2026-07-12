// Helpers de data no formato aceito pela API (AAAA-MM-DD) e exibição BR.

export function toApiDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function todayApi() {
  return toApiDate(new Date());
}

// "2026-07-13" -> "13/07/2026"
export function apiToBR(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

// "09:00:00" -> "09:00"
export function hhmm(t) {
  if (!t) return '';
  return t.slice(0, 5);
}

export const WEEKDAYS = [
  'Segunda',
  'Terça',
  'Quarta',
  'Quinta',
  'Sexta',
  'Sábado',
  'Domingo',
];

export function money(v) {
  return `R$ ${Number(v || 0).toFixed(2).replace('.', ',')}`;
}
