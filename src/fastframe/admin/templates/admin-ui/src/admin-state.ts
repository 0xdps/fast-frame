import { createContext, useContext } from "react";

import type { ModelSchema, SiteBranding } from "./api";

export type ThemeName = "light" | "dark";

export interface AdminContextValue {
  models: ModelSchema[];
  site: SiteBranding;
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  compact: boolean;
  setCompact: (compact: boolean) => void;
  sidebarFolded: boolean;
  setSidebarFolded: (folded: boolean) => void;
  refreshKey: number;
  refresh: () => void;
}

export const AdminContext = createContext<AdminContextValue | null>(null);

export function useAdmin(): AdminContextValue {
  const value = useContext(AdminContext);
  if (!value) throw new Error("useAdmin must be used inside AdminProvider");
  return value;
}

function readFlag(key: string): boolean {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
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

export function initialCompact(): boolean {
  return readFlag("frame.density");
}

export function initialSidebarFolded(): boolean {
  return readFlag("frame.sidebar");
}
