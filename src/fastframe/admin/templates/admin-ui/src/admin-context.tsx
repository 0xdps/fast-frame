import { useEffect, useMemo, useState, type ReactNode } from "react";

import type { ModelSchema, SiteBranding } from "./api";
import { AdminContext, initialCompact, initialSidebarFolded, initialTheme, type ThemeName } from "./admin-state";

export function AdminProvider({
  models,
  site,
  children,
}: {
  models: ModelSchema[];
  site: SiteBranding;
  children: ReactNode;
}) {
  const [theme, setThemeState] = useState<ThemeName>(initialTheme);
  const [compact, setCompactState] = useState(initialCompact);
  const [sidebarFolded, setSidebarFoldedState] = useState(initialSidebarFolded);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    if (compact) document.documentElement.dataset.density = "compact";
    else delete document.documentElement.dataset.density;
    if (sidebarFolded) document.documentElement.dataset.sidebar = "folded";
    else delete document.documentElement.dataset.sidebar;
  }, [theme, compact, sidebarFolded]);

  const value = useMemo(
    () => ({
      models,
      site,
      theme,
      setTheme: (next: ThemeName) => {
        setThemeState(next);
        try {
          localStorage.setItem("frame.theme", next);
        } catch {
          /* ignore */
        }
      },
      compact,
      setCompact: (next: boolean) => {
        setCompactState(next);
        try {
          localStorage.setItem("frame.density", next ? "1" : "0");
        } catch {
          /* ignore */
        }
      },
      sidebarFolded,
      setSidebarFolded: (next: boolean) => {
        setSidebarFoldedState(next);
        try {
          localStorage.setItem("frame.sidebar", next ? "1" : "0");
        } catch {
          /* ignore */
        }
      },
      refreshKey,
      refresh: () => setRefreshKey((key) => key + 1),
    }),
    [models, site, theme, compact, sidebarFolded, refreshKey],
  );

  return <AdminContext.Provider value={value}>{children}</AdminContext.Provider>;
}
