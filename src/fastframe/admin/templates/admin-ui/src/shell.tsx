import { useEffect, useMemo, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import type { ModelSchema } from "./api";
import { useAdmin } from "./admin-state";
import { CommandPalette } from "./components/command-palette";
import { Switch } from "./components/ui/switch";
import { useCurrentUser } from "./currentUser";
import { cn } from "./lib/cn";
import { logout } from "./lib/client";
import { initials, isUserModel, toneFor } from "./lib/format";

const ADMIN_GROUP = "Admin";

function navLabel(model: ModelSchema): string {
  if (model.resource === "auditlog") return "Activity";
  if (model.resource === "group" || model.name === "Group") return "Roles";
  return model.labelPlural;
}

function navIcon(model: ModelSchema): "rows" | "users" | "shield" | "history" {
  if (model.resource === "auditlog") return "history";
  if (model.resource === "user" || model.name === "User") return "users";
  if (model.resource === "group" || model.name === "Group") return "shield";
  return "rows";
}

function groupByApp(models: ModelSchema[]): Map<string, ModelSchema[]> {
  const grouped = new Map<string, ModelSchema[]>();
  const admin: ModelSchema[] = [];
  for (const model of models) {
    if (model.navGroup === ADMIN_GROUP) {
      admin.push(model);
      continue;
    }
    const label = model.appLabel || "app";
    const bucket = grouped.get(label) ?? [];
    bucket.push(model);
    grouped.set(label, bucket);
  }
  if (admin.length) {
    const order = ["user", "group", "auditlog"];
    admin.sort((a, b) => {
      const left = order.indexOf(a.resource);
      const right = order.indexOf(b.resource);
      return (left === -1 ? order.length : left) - (right === -1 ? order.length : right);
    });
    grouped.set(ADMIN_GROUP, admin);
  }
  return grouped;
}

function pageTitle(pathname: string, models: ModelSchema[]): string {
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 0) return "Overview";
  const model = models.find((item) => item.resource === parts[0]);
  if (!model) return "FastFrame Admin";
  if (parts[1] === "create") return `New ${model.label}`;
  if (parts[1]) return model.label;
  return model.labelPlural;
}

function Mark() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" className="shrink-0">
      <rect width="24" height="24" rx="7" className="fill-accent" />
      <path
        d="M7.5 16.5 12 7.5l4.5 9M9.4 13.2h5.2"
        fill="none"
        className="stroke-accent-foreground"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function Icon({
  name,
}: {
  name: "overview" | "rows" | "users" | "shield" | "history" | "search" | "sidebar" | "moon" | "compact" | "sign-out" | "user";
}) {
  const common = {
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (name === "overview") {
    return (
      <svg {...common}>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    );
  }
  if (name === "users") {
    return (
      <svg {...common}>
        <circle cx="9" cy="8" r="3" />
        <path d="M3.5 19a5.5 5.5 0 0 1 11 0" />
        <circle cx="17" cy="9" r="2.2" />
        <path d="M16 14.2a4.2 4.2 0 0 1 4.5 4" />
      </svg>
    );
  }
  if (name === "shield") {
    return (
      <svg {...common}>
        <path d="M12 3 5 6v6c0 4.2 2.8 7.2 7 8.5 4.2-1.3 7-4.3 7-8.5V6z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    );
  }
  if (name === "history") {
    return (
      <svg {...common}>
        <path d="M4 12a8 8 0 1 0 2.2-5.5" />
        <path d="M4 4v4h4M12 8v5l3 2" />
      </svg>
    );
  }
  if (name === "search") {
    return (
      <svg {...common}>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
    );
  }
  if (name === "sidebar") {
    return (
      <svg {...common}>
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M9 4v16" />
      </svg>
    );
  }
  if (name === "moon") {
    return (
      <svg {...common}>
        <path d="M20 14.5A8 8 0 1 1 9.5 4 6.5 6.5 0 0 0 20 14.5z" />
      </svg>
    );
  }
  if (name === "compact") {
    return (
      <svg {...common}>
        <path d="M4 8h16M4 12h16M4 16h10" />
      </svg>
    );
  }
  if (name === "sign-out") {
    return (
      <svg {...common}>
        <path d="M9 6H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h3" />
        <path d="M14 16l4-4-4-4M18 12H9" />
      </svg>
    );
  }
  if (name === "user") {
    return (
      <svg {...common}>
        <circle cx="12" cy="8" r="3" />
        <path d="M5 19a7 7 0 0 1 14 0" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <path d="M4 6h16M4 12h16M4 18h12" />
    </svg>
  );
}

function SideLink({
  to,
  label,
  end = false,
  icon,
}: {
  to: string;
  label: string;
  end?: boolean;
  icon: "overview" | "rows" | "users" | "shield" | "history";
}) {
  return (
    <NavLink
      to={to}
      end={end}
      title={label}
      className={({ isActive }) =>
        cn(
          "flex h-8.5 items-center gap-2.5 rounded-field border px-2.5 font-medium folded:lg:justify-center folded:lg:px-0",
          isActive
            ? "border-border bg-card text-foreground shadow-quiet"
            : "border-transparent text-foreground/80 hover:bg-card/70 hover:text-foreground",
        )
      }
    >
      {({ isActive }) => (
        <>
          <span className={cn("inline-flex size-4 shrink-0 items-center justify-center", isActive ? "text-foreground" : "text-muted-foreground")}>
            <Icon name={icon} />
          </span>
          <span className="truncate folded:lg:sr-only">{label}</span>
        </>
      )}
    </NavLink>
  );
}

function AccountMenu({ models }: { models: ModelSchema[] }) {
  const user = useCurrentUser();
  const { theme, setTheme, compact, setCompact } = useAdmin();
  const name = user?.username || user?.email || "Account";
  const tone = toneFor(name);
  const userModel = models.find(isUserModel);
  const profile = user?.id != null && userModel ? `/${userModel.resource}/${user.id}` : undefined;

  const signOut = async () => {
    try {
      await logout();
    } finally {
      window.location.reload();
    }
  };

  return (
    <div className="border-t border-border pt-2.5">
      <details className="group relative">
        <summary
          className="flex w-full cursor-pointer list-none items-center gap-2.5 rounded-field border border-border bg-card p-1.5 shadow-quiet hover:bg-card/70 folded:lg:justify-center folded:lg:p-0.5 [&::-webkit-details-marker]:hidden"
          title={name}
        >
          <span
            className="inline-flex size-7 shrink-0 items-center justify-center rounded-full text-note font-semibold text-white"
            style={{ background: tone }}
            aria-hidden="true"
          >
            {user ? initials(undefined, undefined, name) : <Icon name="user" />}
          </span>
          <span className="min-w-0 flex-1 truncate font-medium folded:lg:sr-only">{user ? name : "Settings"}</span>
          <span className="text-muted-foreground folded:lg:hidden" aria-hidden="true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m7 15 5 5 5-5M7 9l5-5 5 5" />
            </svg>
          </span>
        </summary>
        <div className="absolute inset-x-0 bottom-full z-30 mb-1.5 rounded-box border border-border bg-card p-1.5 shadow-float folded:lg:start-full folded:lg:bottom-0 folded:lg:mb-0 folded:lg:ms-2 folded:lg:w-56">
          <div className="flex items-center gap-2 rounded-field px-2 py-1.5 text-label">
            <span className="text-muted-foreground"><Icon name="moon" /></span>
            <span className="flex-1">Dark mode</span>
            <Switch
              checked={theme === "dark"}
              aria-label="Dark mode"
              onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
            />
          </div>
          <div className="flex items-center gap-2 rounded-field px-2 py-1.5 text-label">
            <span className="text-muted-foreground"><Icon name="compact" /></span>
            <span className="flex-1">Compact mode</span>
            <Switch checked={compact} aria-label="Compact mode" onCheckedChange={setCompact} />
          </div>
          {profile ? (
            <NavLink to={profile} className="mt-1 flex items-center gap-2 rounded-field border-t border-border px-2 py-2 text-label hover:bg-subtle">
              <span className="text-muted-foreground"><Icon name="user" /></span>
              My profile
            </NavLink>
          ) : null}
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-field px-2 py-2 text-start text-label hover:bg-subtle"
            onClick={() => void signOut()}
          >
            <span className="text-muted-foreground"><Icon name="sign-out" /></span>
            Sign out
          </button>
        </div>
      </details>
    </div>
  );
}

export function Shell() {
  const { models, site, sidebarFolded, setSidebarFolded } = useAdmin();
  const { pathname } = useLocation();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    document.title = `${pageTitle(pathname, models)} · ${site.title}`;
    setDrawerOpen(false);
  }, [pathname, models, site.title]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const menuModels = useMemo(
    () => models.filter((model) => model.showInNavigation !== false),
    [models],
  );
  const grouped = useMemo(() => groupByApp(menuModels), [menuModels]);

  useEffect(() => {
    const links = navRef.current;
    if (!links) return;
    const open = links.querySelector<HTMLElement>('[aria-current="page"]');
    if (open && open.offsetTop + open.offsetHeight > links.clientHeight) {
      links.scrollTop = open.offsetTop - (links.clientHeight - open.offsetHeight) / 2;
    }
    const markEdges = () => {
      links.toggleAttribute("data-more-above", links.scrollTop > 1);
      links.toggleAttribute("data-more-below", links.scrollTop + links.clientHeight < links.scrollHeight - 1);
    };
    markEdges();
    links.addEventListener("scroll", markEdges, { passive: true });
    return () => links.removeEventListener("scroll", markEdges);
  }, [grouped, pathname]);

  const sidebar = (
    <aside className="flex h-full w-60 flex-col gap-3.5 overflow-visible bg-background px-2.5 py-3.5 lg:w-58 folded:lg:w-14">
      <div className="flex items-center gap-1 folded:lg:flex-col folded:lg:gap-2.5">
        <NavLink to="/" end className="flex h-8 min-w-0 flex-1 items-center gap-2.5 px-1.5 folded:lg:flex-none" title={site.header}>
          <Mark />
          <span className="truncate text-[15px] font-semibold tracking-tight folded:lg:sr-only">{site.header}</span>
        </NavLink>
        <button
          type="button"
          className="hidden size-8 items-center justify-center rounded-field text-muted-foreground hover:bg-card hover:text-foreground lg:inline-flex"
          aria-label={sidebarFolded ? "Unfold the sidebar" : "Fold the sidebar"}
          title={sidebarFolded ? "Unfold the sidebar" : "Fold the sidebar"}
          onClick={() => setSidebarFolded(!sidebarFolded)}
        >
          <Icon name="sidebar" />
        </button>
      </div>

      <button
        type="button"
        className="flex h-8.5 items-center gap-2 rounded-field border border-border bg-card ps-2.5 pe-1.5 text-muted-foreground shadow-quiet hover:text-foreground folded:lg:justify-center folded:lg:px-0"
        aria-label="Search, or press Control K"
        title="Search, or press Control K"
        onClick={() => setPaletteOpen(true)}
      >
        <Icon name="search" />
        <span className="flex-1 text-start folded:lg:hidden">Search</span>
        <kbd className="rounded border border-border bg-background px-1 font-mono text-caption text-muted-foreground folded:lg:hidden">
          Ctrl K
        </kbd>
      </button>

      <nav ref={navRef} id="sidebar-links" className="menu-scroll relative flex min-h-0 flex-1 flex-col overflow-x-hidden overflow-y-auto" aria-label="Main">
        <ul className="flex flex-col gap-0.5">
          <li>
            <SideLink to="/" label="Overview" end icon="overview" />
          </li>
        </ul>
        {[...grouped.entries()].map(([appLabel, appModels], index) => (
          <div key={appLabel}>
            <p className="px-2.5 pt-4 pb-1 text-note font-medium tracking-wide text-muted-foreground uppercase folded:lg:sr-only" id={`nav-group-${index}`}>
              {appLabel}
            </p>
            <ul className="mt-0.5 flex flex-col gap-0.5 folded:lg:mt-2.5 folded:lg:border-t folded:lg:border-border folded:lg:pt-2.5" aria-labelledby={`nav-group-${index}`}>
              {appModels.map((model) => (
                <li key={model.resource}>
                  <SideLink to={`/${model.resource}`} label={navLabel(model)} icon={navIcon(model)} />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <AccountMenu models={models} />
    </aside>
  );

  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:fixed focus:start-3 focus:top-3 focus:z-[60] focus:rounded-field focus:bg-primary focus:px-3 focus:py-1.5 focus:text-primary-foreground"
      >
        Skip to the content
      </a>

      <div className="hidden h-full shrink-0 lg:block">{sidebar}</div>

      {drawerOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button type="button" className="absolute inset-0 bg-[#1a1a18]/40" aria-label="Close the menu" onClick={() => setDrawerOpen(false)} />
          <div className="relative h-full w-60 shadow-float">{sidebar}</div>
        </div>
      ) : null}

      <div className="flex h-dvh min-w-0 flex-1 flex-col lg:py-2 lg:pe-2">
        <main
          id="content"
          tabIndex={-1}
          className="group/page flex min-h-0 flex-1 flex-col bg-card focus:outline-none lg:overflow-hidden lg:rounded-box lg:border lg:border-border lg:shadow-panel"
        >
          <Outlet context={{ openMenu: () => setDrawerOpen(true), openPalette: () => setPaletteOpen(true) }} />
        </main>
      </div>

      <CommandPalette open={paletteOpen} models={models} onOpenChange={setPaletteOpen} />
    </div>
  );
}
