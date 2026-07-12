// Gerencia a URL do backend (nuvem) de forma persistente.
// O admin cola a URL do Render uma vez na tela de Configurações e ela fica
// salva no dispositivo — sem precisar recompilar o APK.
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = '@barbearia/api_url';

// Valor inicial: variável de ambiente do build ou localhost (dev).
const DEFAULT_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

let cached = null;

export async function getApiUrl() {
  if (cached) return cached;
  try {
    const saved = await AsyncStorage.getItem(KEY);
    cached = (saved && saved.trim()) || DEFAULT_URL;
  } catch (e) {
    cached = DEFAULT_URL;
  }
  return cached.replace(/\/+$/, ''); // remove barra final
}

export async function setApiUrl(url) {
  cached = (url || '').trim();
  await AsyncStorage.setItem(KEY, cached);
  return cached;
}

export { DEFAULT_URL };
