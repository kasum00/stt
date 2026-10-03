"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ApiError, User } from "@/lib/api";
import { clearTokens } from "@/lib/auth/token-store";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  user: User | null;
  status: AuthStatus;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  reloadUser: () => Promise<User | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const reloadUser = useCallback(async () => {
    try {
      const currentUser = await api.getMe();
      setUser(currentUser);
      setStatus("authenticated");
      return currentUser;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearTokens();
        setUser(null);
        setStatus("unauthenticated");
        return null;
      }

      // Keep an existing authenticated session during transient API failures.
      setStatus((current) => current === "authenticated" ? current : "unauthenticated");
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;
    const handleAuthCleared = () => {
      if (!active) return;
      setUser(null);
      setStatus("unauthenticated");
    };

    window.addEventListener("herstyleai:auth-cleared", handleAuthCleared);
    queueMicrotask(() => {
      if (!active) return;
      void api.refresh()
        .then(() => reloadUser())
        .catch((error) => {
          if (!active) return;
          if (error instanceof ApiError && error.status === 401) {
            clearTokens();
            setUser(null);
          }
          setStatus("unauthenticated");
        });
    });

    return () => {
      active = false;
      window.removeEventListener("herstyleai:auth-cleared", handleAuthCleared);
    };
  }, [reloadUser]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    status,
    isAuthenticated: status === "authenticated",
    async login(email, password) {
      setStatus("loading");
      await api.login(email, password);
      const currentUser = await reloadUser();
      if (!currentUser) throw new Error("Không thể khôi phục phiên đăng nhập.");
      return currentUser;
    },
    async register(email, password) {
      return api.register(email, password);
    },
    async logout() {
      try {
        await api.logout();
      } finally {
        clearTokens();
        setUser(null);
        setStatus("unauthenticated");
      }
    },
    async changePassword(currentPassword, newPassword) {
      await api.changePassword(currentPassword, newPassword);
      clearTokens();
      setUser(null);
      setStatus("unauthenticated");
    },
    reloadUser,
  }), [reloadUser, status, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
