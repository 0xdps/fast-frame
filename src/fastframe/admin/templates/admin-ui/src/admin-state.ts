import { createContext, useContext } from "react";

import type { ModelSchema } from "./api";

export type ThemeName = "light" | "dark";

export interface AdminContextValue {
  models: ModelSchema[];
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  refreshKey: number;
  refresh: () => void;
}

export const AdminContext = createContext<AdminContextValue | null>(null);

export function useAdmin(): AdminContextValue {
  const value = useContext(AdminContext);
  if (!value) throw new Error("useAdmin must be used inside AdminProvider");
  return value;
}

export function initialTheme(): ThemeName {
  try {
    const saved = localStorage.getItem("frame.theme");
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    /* private mode */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
