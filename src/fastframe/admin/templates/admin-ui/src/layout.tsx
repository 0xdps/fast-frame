import { useState } from "react";
import { MenuList } from "@mui/material";
import {
  AppBar,
  DashboardMenuItem,
  Layout,
  LoadingIndicator,
  MenuItemLink,
  useSidebarState,
  useStore,
  type LayoutProps,
} from "react-admin";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SearchIcon from "@mui/icons-material/Search";
import ViewListOutlinedIcon from "@mui/icons-material/ViewListOutlined";

import type { ModelSchema } from "./api";
import { makeUserMenu } from "./userMenu";

/**
 * Audit history is reached from the dashboard's "Recent activity" panel,
 * not from the model list — it's a log of other models, not a model you
 * manage alongside them.
 */
const HIDDEN_FROM_SIDEBAR = new Set(["auditlog"]);

function sidebarModels(models: ModelSchema[]): ModelSchema[] {
  return models.filter((model) => !HIDDEN_FROM_SIDEBAR.has(model.resource));
}

function groupByApp(models: ModelSchema[]): Map<string, ModelSchema[]> {
  const grouped = new Map<string, ModelSchema[]>();
  for (const model of models) {
    const label = model.appLabel || "app";
    const bucket = grouped.get(label) ?? [];
    bucket.push(model);
    grouped.set(label, bucket);
  }
  return grouped;
}

function matchesQuery(model: ModelSchema, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    model.labelPlural.toLowerCase().includes(q) ||
    model.label.toLowerCase().includes(q) ||
    model.resource.toLowerCase().includes(q)
  );
}

function ModelLink({ model }: { model: ModelSchema }) {
  return (
    <MenuItemLink
      to={`/${model.resource}`}
      primaryText={model.labelPlural}
      leftIcon={<ViewListOutlinedIcon fontSize="small" />}
    />
  );
}

/** One collapsible app section in the sidebar. Open state persists (per browser) via react-admin's store. */
function AppSection({
  appLabel,
  models,
  forceOpen,
}: {
  appLabel: string;
  models: ModelSchema[];
  forceOpen: boolean;
}) {
  const [collapsedApps, setCollapsedApps] = useStore<string[]>("frame.menu.collapsedApps", []);
  const isCollapsed = !forceOpen && collapsedApps.includes(appLabel);

  const toggle = () => {
    setCollapsedApps((current) =>
      current.includes(appLabel) ? current.filter((label) => label !== appLabel) : [...current, appLabel],
    );
  };

  return (
    <div className="frame-app-section">
      <button type="button" className="frame-app-header" onClick={toggle} aria-expanded={!isCollapsed}>
        <span>{appLabel}</span>
        <ExpandMoreIcon
          className={isCollapsed ? "frame-app-chevron closed" : "frame-app-chevron"}
          fontSize="small"
        />
      </button>
      {isCollapsed ? null : (
        <div className="frame-app-items">
          {models.map((model) => (
            <ModelLink key={model.resource} model={model} />
          ))}
        </div>
      )}
    </div>
  );
}

function makeFrameMenu(models: ModelSchema[]) {
  const menuModels = sidebarModels(models);
  return function FrameMenu() {
    const [query, setQuery] = useState("");
    const [sidebarOpen] = useSidebarState();
    const grouped = groupByApp(menuModels);
    const searching = query.trim().length > 0;

    let filtered = grouped;
    if (searching) {
      filtered = new Map<string, ModelSchema[]>();
      for (const [appLabel, appModels] of grouped) {
        const hits = appModels.filter((model) => matchesQuery(model, query));
        if (hits.length) filtered.set(appLabel, hits);
      }
    }

    return (
      <div className="frame-menu">
        <div className="frame-brand">
          <span className="frame-mark" aria-hidden="true">
            Ff
          </span>
          {sidebarOpen ? (
            <div>
              <div className="frame-name">FastFrame</div>
              <div className="frame-sub">Admin</div>
            </div>
          ) : null}
        </div>

        {sidebarOpen ? (
          <>
            <div className="frame-search">
              <SearchIcon fontSize="small" aria-hidden="true" />
              <input
                type="search"
                placeholder="Search models…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                aria-label="Search models"
              />
            </div>
            <MenuList className="frame-menu-scroll">
              <DashboardMenuItem primaryText="Overview" />
              {[...filtered.entries()].map(([appLabel, appModels]) => (
                <AppSection key={appLabel} appLabel={appLabel} models={appModels} forceOpen={searching} />
              ))}
              {searching && filtered.size === 0 ? (
                <p className="frame-menu-empty">No models match &ldquo;{query}&rdquo;.</p>
              ) : null}
            </MenuList>
          </>
        ) : (
          // Collapsed (icon-only) sidebar: skip grouping/search, just list every model.
          <MenuList className="frame-menu-scroll">
            <DashboardMenuItem primaryText="Overview" />
            {menuModels.map((model) => (
              <ModelLink key={model.resource} model={model} />
            ))}
          </MenuList>
        )}
      </div>
    );
  };
}

export function makeFrameLayout(models: ModelSchema[]) {
  const FrameMenu = makeFrameMenu(models);
  const UserMenu = makeUserMenu(models);
  // Skip the default toolbar's theme toggle — dark mode lives in the user menu instead.
  const FrameAppBar = () => (
    <AppBar color="inherit" elevation={0} toolbar={<LoadingIndicator />} userMenu={<UserMenu />} />
  );

  return function FrameLayout(props: LayoutProps) {
    return <Layout {...props} appBar={FrameAppBar} menu={FrameMenu} />;
  };
}
