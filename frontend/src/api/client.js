// Cliente HTTP simples para a API FastAPI.
//
// Defina a URL da API via variável de ambiente do Expo:
//   EXPO_PUBLIC_API_URL=http://SEU_IP:8000
// Caso não definida, usa localhost (útil no emulador / web).

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// Serviços padrão usados como fallback quando a API está indisponível
// (permite que o app funcione offline / sem back-end no ambiente inicial).
const FALLBACK_SERVICES = [
  { id: 1, name: 'Corte de Cabelo', description: 'Corte masculino tradicional ou moderno', price: 35, duration_minutes: 30 },
  { id: 2, name: 'Barba', description: 'Aparo e modelagem de barba com toalha quente', price: 25, duration_minutes: 30 },
  { id: 3, name: 'Corte + Barba', description: 'Combo completo corte e barba', price: 55, duration_minutes: 60 },
  { id: 4, name: 'Sobrancelha', description: 'Design e limpeza de sobrancelha', price: 15, duration_minutes: 15 },
  { id: 5, name: 'Pézinho / Acabamento', description: 'Acabamento e contorno', price: 15, duration_minutes: 15 },
];

export async function getServices() {
  try {
    const res = await fetch(`${API_URL}/services`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return Array.isArray(data) && data.length ? data : FALLBACK_SERVICES;
  } catch (err) {
    // Sem back-end disponível: retorna a lista padrão.
    return FALLBACK_SERVICES;
  }
}

export async function createAppointment(appointment) {
  const res = await fetch(`${API_URL}/appointments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(appointment),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export { API_URL };
