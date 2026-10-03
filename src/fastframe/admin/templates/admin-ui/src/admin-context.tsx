import { useEffect, useMemo, useState, type ReactNode } from "react";

import type { ModelSchema, SiteBranding } from "./api";
import { AdminContext, initialTheme, type ThemeName } from "./admin-state";

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
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

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
      refreshKey,
      refresh: () => setRefreshKey((key) => key + 1),
    }),
    [models, site, theme, refreshKey],
  );

  return <AdminContext.Provider value={value}>{children}</AdminContext.Provider>;
}
