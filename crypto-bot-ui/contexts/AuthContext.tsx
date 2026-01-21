'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthState {
  isLoggedIn: boolean;
  apiKey: string;
  apiSecret: string;
  isTestnet: boolean;
}

interface AuthContextType {
  auth: AuthState;
  login: (apiKey: string, apiSecret: string, isTestnet: boolean) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({
    isLoggedIn: false,
    apiKey: '',
    apiSecret: '',
    isTestnet: true,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('binance_auth');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setAuth({ ...parsed, isLoggedIn: true });
      } catch {
        // Invalid data
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (apiKey: string, apiSecret: string, isTestnet: boolean): Promise<boolean> => {
    setIsLoading(true);

    try {
      // Test API connection
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey, apiSecret, isTestnet }),
      });

      const data = await response.json();

      if (data.success) {
        const newAuth = {
          isLoggedIn: true,
          apiKey,
          apiSecret,
          isTestnet,
        };
        setAuth(newAuth);
        localStorage.setItem('binance_auth', JSON.stringify({
          apiKey,
          apiSecret,
          isTestnet,
        }));
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setAuth({
      isLoggedIn: false,
      apiKey: '',
      apiSecret: '',
      isTestnet: true,
    });
    localStorage.removeItem('binance_auth');
  };

  return (
    <AuthContext.Provider value={{ auth, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
