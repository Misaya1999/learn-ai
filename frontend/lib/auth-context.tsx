"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getCurrentUser, loginAccount, type User } from "./api";

const TOKEN_KEY = "learnai_access_token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  ready: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (!storedToken) {
      queueMicrotask(() => setReady(true));
      return;
    }

    getCurrentUser(storedToken)
      .then((currentUser) => {
        setToken(storedToken);
        setUser(currentUser);
      })
      .catch(clearSession)
      .finally(() => setReady(true));
  }, [clearSession]);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await loginAccount(email, password);
    const currentUser = await getCurrentUser(result.access_token);
    localStorage.setItem(TOKEN_KEY, result.access_token);
    setToken(result.access_token);
    setUser(currentUser);
    return currentUser;
  }, []);

  const value = useMemo(
    () => ({ user, token, ready, signIn, signOut: clearSession }),
    [user, token, ready, signIn, clearSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
