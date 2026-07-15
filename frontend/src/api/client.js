// Cliente HTTP para a API do SaaS (nuvem).
import { getToken } from '../auth/session';
import { getApiUrl } from '../config';

async function req(path, options = {}) {
  const base = await getApiUrl();
  const token = await getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(base + path, { ...options, headers });
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

// ---- Auth ----
export const register = (data) =>
  req('/auth/register', { method: 'POST', body: JSON.stringify(data) });
export const login = (data) =>
  req('/auth/login', { method: 'POST', body: JSON.stringify(data) });
export const getMe = () => req('/auth/me');
export const changePassword = (data) =>
  req('/auth/change-password', { method: 'POST', body: JSON.stringify(data) });

// ---- Billing ----
export const getPlans = () => req('/billing/plans');
export const getBillingStatus = () => req('/billing/status');
export const subscribe = (data) =>
  req('/billing/subscribe', { method: 'POST', body: JSON.stringify(data) });

// ---- Health ----
export const getHealth = () => req('/health');

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
export const getAvailability = (date, serviceId, barberId) =>
  req(`/appointments/availability?date=${date}${serviceId ? `&service_id=${serviceId}` : ''}${barberId ? `&barber_id=${barberId}` : ''}`);
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

// ---- Planos de corte (assinatura da barbearia) ----
export const getPlansCorte = () => req('/subscription-plans');
export const createPlanCorte = (data) =>
  req('/subscription-plans', { method: 'POST', body: JSON.stringify(data) });
export const deletePlanCorte = (id) =>
  req(`/subscription-plans/${id}`, { method: 'DELETE' });
export const getClientSubs = (clientId) =>
  req(`/client-subscriptions${clientId ? `?client_id=${clientId}` : ''}`);
export const createClientSub = (data) =>
  req('/client-subscriptions', { method: 'POST', body: JSON.stringify(data) });
export const cancelClientSub = (id) =>
  req(`/client-subscriptions/${id}`, { method: 'DELETE' });

// ---- Barbeiros (equipe) ----
export const getStaff = () => req('/staff');
export const createStaff = (data) =>
  req('/staff', { method: 'POST', body: JSON.stringify(data) });
export const deleteStaff = (id) =>
  req(`/staff/${id}`, { method: 'DELETE' });
export const getBarberHours = (id) => req(`/staff/${id}/hours`);
export const setBarberHour = (id, weekday, data) =>
  req(`/staff/${id}/hours/${weekday}`, { method: 'PUT', body: JSON.stringify(data) });
export const resetBarberPassword = (id, new_password) =>
  req(`/staff/${id}/reset-password`, { method: 'POST', body: JSON.stringify({ new_password }) });

// ---- Produtos / estoque / pedidos ----
export const getProducts = () => req('/products');
export const createProduct = (data) =>
  req('/products', { method: 'POST', body: JSON.stringify(data) });
export const updateProduct = (id, data) =>
  req(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteProduct = (id) =>
  req(`/products/${id}`, { method: 'DELETE' });
export const moveStock = (id, data) =>
  req(`/products/${id}/stock`, { method: 'POST', body: JSON.stringify(data) });
export const getOrders = () => req('/orders');
export const updateOrder = (id, status) =>
  req(`/orders/${id}?status=${status}`, { method: 'PATCH' });
