// Armazena a sessão (token JWT + dados da barbearia) de forma persistente.
import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = '@barbearia/token';
const TENANT_KEY = '@barbearia/tenant';

let tokenCache = null;

export async function getToken() {
  if (tokenCache !== null) return tokenCache;
  tokenCache = (await AsyncStorage.getItem(TOKEN_KEY)) || '';
  return tokenCache;
}

export async function setSession(auth) {
  tokenCache = auth.token || tokenCache || '';
  if (auth.token) await AsyncStorage.setItem(TOKEN_KEY, auth.token);
  if (auth.tenant) await AsyncStorage.setItem(TENANT_KEY, JSON.stringify(auth.tenant));
}

export async function getStoredTenant() {
  const raw = await AsyncStorage.getItem(TENANT_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function clearSession() {
  tokenCache = '';
  await AsyncStorage.multiRemove([TOKEN_KEY, TENANT_KEY]);
}
