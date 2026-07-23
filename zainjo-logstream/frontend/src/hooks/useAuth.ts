import { useState, useCallback } from "react";
import api from "../api/client";
import type { Token, UserRead } from "../api/types";

export function useAuth() {
  const [user, setUser] = useState<UserRead | null>(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (username: string, password: string): Promise<void> => {
    const res = await api.post<Token>("/auth/login", { username, password });
    const token = res.data;
    localStorage.setItem("access_token", token.access_token);
    localStorage.setItem("user", JSON.stringify({ username: token.username, role: token.role }));
    setUser({ username: token.username, role: token.role, id: "", is_active: true, created_at: "" });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
    window.location.href = "/login";
  }, []);

  const isAdmin = user?.role === "admin";

  return { user, login, logout, isAdmin, isAuthenticated: !!user };
}
