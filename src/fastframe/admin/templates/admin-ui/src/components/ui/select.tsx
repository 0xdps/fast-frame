import { ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";

import { cn } from "../../lib/cn";

export interface SelectOption {
  value: string;
  label: string;
}

export function SelectField({
  value,
  options,
  onChange,
  disabled,
  ariaLabel,
  searchable,
  query = "",
  onQueryChange,
}: {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  ariaLabel?: string;
  searchable?: boolean;
  query?: string;
  onQueryChange?: (query: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const selected = options.find((option) => option.value === value) ?? options[0];

  useEffect(() => {
    if (disabled) setOpen(false);
  }, [disabled]);

  useEffect(() => {
    if (!open) return;
    const closeOnOutside = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) close();
    };
    window.addEventListener("pointerdown", closeOnOutside);
    return () => window.removeEventListener("pointerdown", closeOnOutside);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const index = Math.max(0, options.findIndex((option) => option.value === value));
    setActive(index);
    searchRef.current?.focus();
  }, [open, value]);

  useEffect(() => {
    setActive((current) => Math.min(current, Math.max(options.length - 1, 0)));
  }, [options.length]);

  const close = () => {
    setOpen(false);
    onQueryChange?.("");
  };

  const choose = (next: string) => {
    onChange(next);
    close();
  };

  const moveActive = (delta: number) => {
    setActive((current) => (current + delta + options.length) % Math.max(options.length, 1));
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) setOpen(true);
      else moveActive(event.key === "ArrowDown" ? 1 : -1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!open) setOpen(true);
      else if (options[active]) choose(options[active].value);
    } else if (event.key === "Escape") {
      close();
    }
  };

  const onSearchKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(event.key === "ArrowDown" ? 1 : -1);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (options[active]) choose(options[active].value);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        disabled={disabled}
        onKeyDown={onKeyDown}
        onClick={() => {
          if (!disabled) setOpen((current) => !current);
        }}
        className={cn(
          "flex h-9 w-full items-center justify-between gap-2 rounded-lg border border-input bg-card px-3 text-left text-sm text-foreground shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:cursor-not-allowed disabled:bg-muted disabled:opacity-100",
          !selected?.value && "text-muted-foreground",
        )}
      >
        <span className="truncate">{selected?.label ?? "Select…"}</span>
        <ChevronDown className={cn("size-4 shrink-0 text-muted-foreground", open && "rotate-180")} />
      </button>
      {open && !disabled ? (
        <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-lg border border-border bg-card shadow-lg">
          {searchable ? (
            <div className="border-b border-border p-1">
              <input
                ref={searchRef}
                type="search"
                value={query}
                placeholder="Search…"
                aria-label={ariaLabel ? `Search ${ariaLabel}` : "Search"}
                onChange={(event) => onQueryChange?.(event.target.value)}
                onKeyDown={onSearchKeyDown}
                className="h-8 w-full rounded-md border border-input bg-card px-2.5 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
          ) : null}
          <ul id={listId} role="listbox" className="select-scroll max-h-60 overflow-y-auto p-1">
            {options.length ? (
              options.map((option, index) => {
                const isSelected = option.value === value;
                return (
                  <li key={`${option.value}:${option.label}`} role="presentation">
                    <button
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      className={cn(
                        "flex w-full items-center rounded-md px-2.5 py-2 text-left text-sm",
                        index === active || isSelected ? "bg-accent text-accent-foreground" : "hover:bg-accent/70",
                      )}
                      onMouseEnter={() => setActive(index)}
                      onClick={() => choose(option.value)}
                    >
                      <span className="truncate">{option.label}</span>
                    </button>
                  </li>
                );
              })
            ) : (
              <li className="px-2.5 py-2 text-sm text-muted-foreground">No matches.</li>
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
