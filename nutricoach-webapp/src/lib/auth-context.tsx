/**
 * lib/auth-context.tsx
 * --------------------
 * Auth context — stores JWT token and user info in localStorage.
 * Provides useAuth() hook to all pages.
 */

"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiGet } from "./api";

interface User {
  id: string;
  full_name: string;
  email: string;
  clinic_name?: string;
  status: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  loading: true,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("nutricoach_token");
    const savedUser = localStorage.getItem("nutricoach_user");

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem("nutricoach_token", newToken);
    localStorage.setItem("nutricoach_user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem("nutricoach_token");
    localStorage.removeItem("nutricoach_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
