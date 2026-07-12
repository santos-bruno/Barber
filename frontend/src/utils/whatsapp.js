import { BUSINESS } from '../constants/business';

/**
 * Monta o link do WhatsApp (wa.me) com o resumo do agendamento.
 *
 * Exemplo de mensagem gerada:
 *   "Olá Sr. Perison, gostaria de agendar Corte + Barba para 12/07/2026 às 14:30.
 *    (Cliente: João)"
 *
 * @param {Object} params
 * @param {string} params.service   Nome do serviço.
 * @param {string} params.date      Data já formatada (ex.: 12/07/2026).
 * @param {string} params.time      Hora já formatada (ex.: 14:30).
 * @param {string} [params.customerName] Nome do cliente (opcional).
 * @returns {string} URL completa do WhatsApp pronta para abrir.
 */
export function buildWhatsAppLink({ service, date, time, customerName }) {
  let message = `Olá Sr. Perison, gostaria de agendar ${service} para ${date} às ${time}.`;

  if (customerName && customerName.trim()) {
    message += ` (Cliente: ${customerName.trim()})`;
  }

  const encoded = encodeURIComponent(message);
  return `https://wa.me/${BUSINESS.whatsappNumber}?text=${encoded}`;
}

/**
 * Formata um objeto Date para DD/MM/AAAA.
 */
export function formatDate(date) {
  const d = String(date.getDate()).padStart(2, '0');
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const y = date.getFullYear();
  return `${d}/${m}/${y}`;
}

/**
 * Formata um objeto Date para HH:MM.
 */
export function formatTime(date) {
  const h = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  return `${h}:${min}`;
}

/**
 * Converte um Date para AAAA-MM-DD (formato aceito pela API).
 */
export function toApiDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
