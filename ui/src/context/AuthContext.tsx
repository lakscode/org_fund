import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "../api";
import type { User, Org } from "../types";

interface AuthState {
  user: User | null;
  token: string | null;
  currentOrg: Org | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  setCurrentOrg: (org: Org) => void;
}

const AuthContext = createContext<AuthState>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [currentOrg, setCurrentOrg] = useState<Org | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      api
        .get("/auth/me")
        .then((res) => {
          setUser(res.data);
          const savedOrgId = localStorage.getItem("currentOrgId");
          const orgs: Org[] = res.data.orgs;
          const saved = orgs.find((o) => o.id === savedOrgId);
          setCurrentOrg(saved || orgs[0] || null);
        })
        .catch(() => {
          localStorage.removeItem("token");
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await api.post("/auth/login", { email, password });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
  };

  const register = async (email: string, name: string, password: string) => {
    const res = await api.post("/auth/register", { email, name, password });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("currentOrgId");
    setToken(null);
    setUser(null);
    setCurrentOrg(null);
  };

  const handleSetCurrentOrg = (org: Org) => {
    setCurrentOrg(org);
    localStorage.setItem("currentOrgId", String(org.id));
  };

  return (
    <AuthContext.Provider
      value={{ user, token, currentOrg, loading, login, register, logout, setCurrentOrg: handleSetCurrentOrg }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
