// Cliente HTTP para a API da barbearia (nuvem).
import { getApiUrl } from '../config';

async function req(path, options = {}) {
  const base = await getApiUrl();
  const res = await fetch(base + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch (e) {}
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---- Info / health ----
export const getInfo = () => req('/info');

// ---- Services ----
export const getServices = () => req('/services');
export const createService = (data) =>
  req('/services', { method: 'POST', body: JSON.stringify(data) });

// ---- Clients ----
export const getClients = (search = '') =>
  req(`/clients${search ? `?search=${encodeURIComponent(search)}` : ''}`);
export const createClient = (data) =>
  req('/clients', { method: 'POST', body: JSON.stringify(data) });
export const getClientAppointments = (id) => req(`/clients/${id}/appointments`);

// ---- Appointments ----
export const getAppointments = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return req(`/appointments${qs ? `?${qs}` : ''}`);
};
export const getAvailability = (date, serviceId) =>
  req(`/appointments/availability?date=${date}${serviceId ? `&service_id=${serviceId}` : ''}`);
export const createAppointment = (data) =>
  req('/appointments', { method: 'POST', body: JSON.stringify(data) });
export const updateAppointment = (id, data) =>
  req(`/appointments/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteAppointment = (id) =>
  req(`/appointments/${id}`, { method: 'DELETE' });

// ---- Cash flow ----
export const getCashflow = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return req(`/cashflow${qs ? `?${qs}` : ''}`);
};
export const getCashSummary = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return req(`/cashflow/summary${qs ? `?${qs}` : ''}`);
};
export const createTransaction = (data) =>
  req('/cashflow', { method: 'POST', body: JSON.stringify(data) });
export const deleteTransaction = (id) =>
  req(`/cashflow/${id}`, { method: 'DELETE' });

// ---- Hours ----
export const getHours = () => req('/hours');
export const updateHour = (weekday, data) =>
  req(`/hours/${weekday}`, { method: 'PUT', body: JSON.stringify(data) });
