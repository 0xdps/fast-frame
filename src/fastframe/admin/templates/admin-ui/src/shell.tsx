import { useEffect, useMemo, useState } from "react";
import { ChevronDown, LayoutDashboard, List, LogOut, Moon, RefreshCw, Search, UserRound } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import type { ModelSchema } from "./api";
import { useAdmin } from "./admin-state";
import { Button } from "./components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./components/ui/dropdown-menu";
import { Switch } from "./components/ui/switch";
import { useCurrentUser } from "./currentUser";
import { cn } from "./lib/cn";
import { logout } from "./lib/client";
import { initials, isUserModel, toneFor } from "./lib/format";

const HIDDEN_FROM_SIDEBAR = new Set(["auditlog"]);

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

function pageTitle(pathname: string, models: ModelSchema[]): string {
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 0) return "Overview";
  const model = models.find((item) => item.resource === parts[0]);
  if (!model) return "FastFrame Admin";
  if (parts[1] === "create") return `Add ${model.label}`;
  if (parts[1]) return model.label;
  return model.labelPlural;
}

function SideLink({ to, label, end = false }: { to: string; label: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      title={label}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm text-[#d5dce6] hover:bg-white/10",
          isActive && "bg-white/15 text-white",
        )
      }
    >
      {to === "/" ? <LayoutDashboard className="size-4 shrink-0" /> : <List className="size-4 shrink-0" />}
      <span className="truncate">{label}</span>
    </NavLink>
  );
}

function AppSection({
  appLabel,
  models,
  forceOpen,
  collapsedApps,
  onToggle,
}: {
  appLabel: string;
  models: ModelSchema[];
  forceOpen: boolean;
  collapsedApps: string[];
  onToggle: (appLabel: string) => void;
}) {
  const collapsed = !forceOpen && collapsedApps.includes(appLabel);
  return (
    <div className="mt-3">
      <button
        type="button"
        className="flex w-full items-center justify-between px-2.5 py-1 text-[11px] font-semibold tracking-wide text-[#8b98ab] uppercase"
        aria-expanded={!collapsed}
        onClick={() => onToggle(appLabel)}
      >
        <span className="truncate">{appLabel}</span>
        <ChevronDown className={cn("size-3.5 transition-transform", collapsed && "-rotate-90")} />
      </button>
      {collapsed ? null : (
        <div className="mt-1 flex flex-col gap-0.5">
          {models.map((model) => (
            <SideLink key={model.resource} to={`/${model.resource}`} label={model.labelPlural} />
          ))}
        </div>
      )}
    </div>
  );
}

function UserMenu({ models }: { models: ModelSchema[] }) {
  const user = useCurrentUser();
  const { theme, setTheme } = useAdmin();
  const navigate = useNavigate();
  if (!user) return <span className="size-8 rounded-full bg-muted" aria-hidden="true" />;

  const name = user.username || user.email || "Account";
  const tone = toneFor(name);
  const userModel = models.find(isUserModel);
  const profile = user.id != null && userModel ? `/${userModel.resource}/${user.id}` : undefined;

  const signOut = async () => {
    try {
      await logout();
    } finally {
      window.location.reload();
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="grid size-8 place-items-center rounded-full text-xs font-semibold text-white"
          style={{ background: tone }}
          aria-label={name}
        >
          {initials(undefined, undefined, name)}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <div className="flex items-center gap-3 px-2.5 py-2">
          <span
            className="grid size-9 place-items-center rounded-full text-sm font-semibold text-white"
            style={{ background: tone }}
            aria-hidden="true"
          >
            {initials(undefined, undefined, name)}
          </span>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium">{name}</div>
            {user.email ? <div className="truncate text-xs text-muted-foreground">{user.email}</div> : null}
          </div>
        </div>
        <DropdownMenuSeparator />
        {profile ? (
          <DropdownMenuItem onSelect={() => navigate(profile)}>
            <UserRound className="size-4" />
            My profile
          </DropdownMenuItem>
        ) : null}
        <DropdownMenuItem onSelect={(event) => event.preventDefault()}>
          <Moon className="size-4" />
          <span className="flex-1">Dark mode</span>
          <Switch
            checked={theme === "dark"}
            aria-label="Dark mode"
            onClick={(event) => event.stopPropagation()}
            onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
          />
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void signOut()}>
          <LogOut className="size-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Shell() {
  const { models, refresh } = useAdmin();
  const { pathname } = useLocation();
  const [query, setQuery] = useState("");
  const [collapsedApps, setCollapsedApps] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem("frame.menu.collapsedApps");
      const parsed = raw ? (JSON.parse(raw) as unknown) : [];
      return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    document.title = `${pageTitle(pathname, models)} · FastFrame`;
  }, [pathname, models]);

  const menuModels = useMemo(
    () => models.filter((model) => !HIDDEN_FROM_SIDEBAR.has(model.resource)),
    [models],
  );
  const grouped = useMemo(() => groupByApp(menuModels), [menuModels]);
  const searching = query.trim().length > 0;
  const filtered = useMemo(() => {
    if (!searching) return grouped;
    const q = query.trim().toLowerCase();
    const next = new Map<string, ModelSchema[]>();
    for (const [appLabel, appModels] of grouped) {
      const hits = appModels.filter((model) =>
        [model.labelPlural, model.label, model.resource].some((value) => value.toLowerCase().includes(q)),
      );
      if (hits.length) next.set(appLabel, hits);
    }
    return next;
  }, [grouped, query, searching]);

  const toggleApp = (appLabel: string) => {
    setCollapsedApps((current) => {
      const next = current.includes(appLabel)
        ? current.filter((label) => label !== appLabel)
        : [...current, appLabel];
      try {
        localStorage.setItem("frame.menu.collapsedApps", JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      <aside className="flex h-full w-[248px] shrink-0 flex-col overflow-hidden bg-[#172033] text-[#d5dce6]">
        <NavLink
          to="/"
          end
          className="flex h-14 shrink-0 items-center gap-2.5 px-3 hover:bg-white/5"
          aria-label="Dashboard"
        >
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-[#3157e8] text-xs font-semibold text-white">
            Ff
          </span>
          <span className="min-w-0">
            <span className="block font-display text-sm font-semibold tracking-tight text-white">FastFrame</span>
            <span className="block text-[11px] text-[#8b98ab]">Admin</span>
          </span>
        </NavLink>

        <div className="mx-3 mb-2 flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-2.5">
          <Search className="size-4 shrink-0 text-[#8b98ab]" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search models…"
            aria-label="Search models"
            className="h-9 w-full bg-transparent text-sm text-[#e7edf6] outline-none placeholder:text-[#8b98ab]"
          />
        </div>

        <nav className="menu-scroll flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto overscroll-none px-2 pb-4">
          <SideLink to="/" label="Overview" end />
          {[...filtered.entries()].map(([appLabel, appModels]) => (
            <AppSection
              key={appLabel}
              appLabel={appLabel}
              models={appModels}
              forceOpen={searching}
              collapsedApps={collapsedApps}
              onToggle={toggleApp}
            />
          ))}
          {searching && filtered.size === 0 ? (
            <p className="px-2.5 py-3 text-sm text-[#8b98ab]">No models match “{query.trim()}”.</p>
          ) : null}
        </nav>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-end gap-2 border-b border-border bg-card px-4">
          <Button type="button" variant="ghost" size="icon" aria-label="Refresh" onClick={refresh}>
            <RefreshCw className="size-4" />
          </Button>
          <UserMenu models={models} />
        </header>
        <main id="main-content" className="min-h-0 flex-1 overflow-y-auto overscroll-none">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
