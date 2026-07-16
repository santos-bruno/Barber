// Identidade visual do app (paleta moderna, tema escuro premium).
export const BUSINESS = {
  appName: 'Agenda Barber',
  developer: 'Bruno',
};

export const COLORS = {
  background: '#0E1014', // fundo profundo
  surface: '#161922', // cards
  surfaceAlt: '#1C2029', // elementos elevados
  cardTop: '#171A23', // topo do card (degradê sutil)
  cardBottom: '#12151D', // base do card
  primary: '#F0C24B', // dourado vibrante
  primaryDark: '#D99A2B',
  text: '#F5F7FB',
  textMuted: '#98A2B3',
  border: '#242A36',
  whatsapp: '#25D366',
  danger: '#FF5C5C',
  info: '#4C8DFF',
  ok: '#3FCB86',
  onPrimary: '#191307', // texto sobre botão dourado
};

// Gradientes (usados com expo-linear-gradient).
export const GRADIENTS = {
  gold: ['#F6D06B', '#D99A2B'],
  header: ['#1B1F27', '#12151B'],
  card: ['#171A23', '#12151D'],
  danger: ['#FF7A7A', '#E24A4A'],
};

// Sombra padrão para dar profundidade.
export const SHADOW = {
  shadowColor: '#000',
  shadowOpacity: 0.32,
  shadowRadius: 16,
  shadowOffset: { width: 0, height: 8 },
  elevation: 8,
};

// Sombra dourada para botões/destaques.
export const SHADOW_GOLD = {
  shadowColor: '#D99A2B',
  shadowOpacity: 0.4,
  shadowRadius: 16,
  shadowOffset: { width: 0, height: 8 },
  elevation: 8,
};
