import { useEffect, useRef, useState } from "react";

import { Button } from "./ui/button";

export function ColumnMenu({
  columns,
  visible,
  onChange,
}: {
  columns: { name: string; label: string }[];
  visible: string[];
  onChange: (visible: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("pointerdown", close);
    return () => window.removeEventListener("pointerdown", close);
  }, [open]);

  const toggle = (name: string) => {
    const next = visible.includes(name) ? visible.filter((item) => item !== name) : [...visible, name];
    const ordered = columns.map((column) => column.name).filter((item) => next.includes(item));
    onChange(ordered.length ? ordered : [name]);
  };

  return (
    <div ref={rootRef} className="relative">
      <Button type="button" variant="outline" size="sm" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
        Columns
      </Button>
      {open ? (
        <ul className="absolute end-0 z-20 mt-1 w-56 rounded-box border border-border bg-card p-1.5 shadow-float">
          {columns.map((column) => {
            const checked = visible.includes(column.name);
            return (
              <li key={column.name}>
                <label className="flex cursor-pointer items-center gap-2 rounded-field px-2 py-1.5 text-label hover:bg-subtle">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggle(column.name)}
                  />
                  <span className="truncate">{column.label}</span>
                </label>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
