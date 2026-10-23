import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { ModelSchema } from "../api";

export function CommandPalette({
  open,
  models,
  onOpenChange,
}: {
  open: boolean;
  models: ModelSchema[];
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  const items = useMemo(() => {
    const q = query.trim().toLowerCase();
    const pages = [{ to: "/", label: "Overview", hint: "Dashboard" }];
    for (const model of models) {
      if (model.showInNavigation === false) continue;
      pages.push({
        to: `/${model.resource}`,
        label: model.resource === "auditlog" ? "Activity" : model.resource === "group" ? "Roles" : model.labelPlural,
        hint: model.navGroup || model.appLabel || "Model",
      });
    }
    if (!q) return pages;
    return pages.filter((item) => `${item.label} ${item.hint}`.toLowerCase().includes(q));
  }, [models, query]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    const frame = window.requestAnimationFrame(() => inputRef.current?.focus());
    return () => window.cancelAnimationFrame(frame);
  }, [open]);

  useEffect(() => {
    setActive(0);
  }, [query]);

  if (!open) return null;

  const go = (to: string) => {
    navigate(to);
    onOpenChange(false);
  };

  return (
    <div className="fixed inset-0 z-50" role="presentation">
      <button
        type="button"
        className="absolute inset-0 bg-[#1a1a18]/40"
        aria-label="Close"
        onClick={() => onOpenChange(false)}
      />
      <div
        role="dialog"
        aria-label="Go to a page"
        className="relative mx-auto mt-16 w-[min(100%-2rem,36rem)] overflow-hidden rounded-box border border-border bg-card text-card-foreground shadow-float"
      >
        <label className="flex h-12 items-center gap-2 border-b border-border px-3">
          <SearchIcon />
          <input
            ref={inputRef}
            type="search"
            value={query}
            role="combobox"
            aria-expanded="true"
            aria-controls="palette-results"
            aria-label="Go to a page"
            placeholder="Go to a page"
            className="h-full w-full bg-transparent text-[15px] outline-none placeholder:text-faint"
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActive((current) => Math.min(current + 1, Math.max(items.length - 1, 0)));
              } else if (event.key === "ArrowUp") {
                event.preventDefault();
                setActive((current) => Math.max(current - 1, 0));
              } else if (event.key === "Enter" && items[active]) {
                event.preventDefault();
                go(items[active].to);
              } else if (event.key === "Escape") {
                onOpenChange(false);
              }
            }}
          />
          <kbd className="rounded-field border border-border bg-background px-1.5 py-0.5 font-mono text-caption text-muted-foreground">
            Esc
          </kbd>
        </label>
        <ul id="palette-results" role="listbox" className="max-h-96 overflow-auto p-1.5">
          {items.length === 0 ? (
            <li className="px-2.5 py-3 text-label text-muted-foreground">No pages match “{query.trim()}”.</li>
          ) : (
            items.map((item, index) => (
              <li key={item.to} role="option" aria-selected={index === active}>
                <button
                  type="button"
                  className={`flex w-full items-center gap-3 rounded-field px-2.5 py-2 text-start text-label ${
                    index === active ? "bg-subtle" : "hover:bg-subtle"
                  }`}
                  onMouseEnter={() => setActive(index)}
                  onClick={() => go(item.to)}
                >
                  <span className="min-w-0 flex-1 truncate font-medium">{item.label}</span>
                  <span className="shrink-0 text-note text-muted-foreground">{item.hint}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="shrink-0 text-muted-foreground" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}
