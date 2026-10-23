import type { ReactNode } from "react";

import { cn } from "../lib/cn";

export function PageHeader({
  title,
  meta,
  actions,
  breadcrumb,
  messages,
  onOpenMenu,
  onOpenPalette,
}: {
  title: string;
  meta?: ReactNode;
  actions?: ReactNode;
  breadcrumb?: ReactNode;
  messages?: ReactNode;
  onOpenMenu?: () => void;
  onOpenPalette?: () => void;
}) {
  return (
    <div className="shrink-0">
      {breadcrumb ? (
        <nav aria-label="Breadcrumb" className="flex h-11 items-end gap-1.5 px-4 text-label text-muted-foreground lg:px-7">
          {breadcrumb}
        </nav>
      ) : null}
      <header
        className={cn(
          "flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-transparent px-4 py-4 lg:px-7",
          "in-data-[scrolled=true]:border-line compact:py-3",
        )}
      >
        {onOpenMenu ? (
          <button
            type="button"
            className="inline-flex size-8 items-center justify-center rounded-field text-foreground hover:bg-subtle lg:hidden"
            aria-label="Open the menu"
            onClick={onOpenMenu}
          >
            <MenuIcon />
          </button>
        ) : null}
        <div className="min-w-0 max-w-full flex-1 sm:flex-[1_0_auto]">
          <div className="flex min-w-0 items-baseline gap-2.5 compact:gap-2">
            <h1 className="min-w-0 truncate text-[22px] leading-tight font-semibold tracking-tight compact:text-[18px]">
              {title}
            </h1>
            {meta ? <div className="shrink-0 text-note text-muted-foreground">{meta}</div> : null}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {onOpenPalette ? (
            <button
              type="button"
              className="inline-flex size-8 items-center justify-center rounded-field text-muted-foreground hover:bg-subtle hover:text-foreground lg:hidden"
              aria-label="Search, or press Control K"
              onClick={onOpenPalette}
            >
              <SearchIcon />
            </button>
          ) : null}
          {actions}
        </div>
        {messages ? <div className="flex basis-full flex-col gap-2">{messages}</div> : null}
      </header>
    </div>
  );
}

function MenuIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}
