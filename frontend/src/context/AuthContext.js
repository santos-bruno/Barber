import React, { createContext, useContext, useEffect, useState } from 'react';

import { getMe } from '../api/client';
import { clearSession, getStoredTenant, getToken, setSession } from '../auth/session';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState('');
  const [tenant, setTenant] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    (async () => {
      const t = await getToken();
      if (t) {
        setToken(t);
        setTenant(await getStoredTenant());
        // Revalida em segundo plano (atualiza status da assinatura).
        try {
          const me = await getMe();
          setTenant(me.tenant);
          setUser(me.user);
          await setSession({ tenant: me.tenant });
        } catch (e) {
          // token inválido/expirado
          if (e.status === 401) {
            await clearSession();
            setToken('');
            setTenant(null);
          }
        }
      }
      setLoading(false);
    })();
  }, []);

  const signIn = async (auth) => {
    await setSession(auth);
    setToken(auth.token);
    setTenant(auth.tenant);
    setUser(auth.user);
  };

  const signOut = async () => {
    await clearSession();
    setToken('');
    setTenant(null);
    setUser(null);
  };

  const refreshTenant = async () => {
    try {
      const me = await getMe();
      setTenant(me.tenant);
      await setSession({ tenant: me.tenant });
    } catch (e) {}
  };

  return (
    <AuthContext.Provider
      value={{ loading, token, tenant, user, signIn, signOut, refreshTenant, isAuthed: !!token }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
