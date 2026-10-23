import { useEffect, useState } from "react";

import type { FieldSchema, ModelSchema } from "../api";
import { fieldChoices, listFilters, type ListFilter } from "../lib/client";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

const SHORTCUT_LABEL: Record<string, string> = {
  today: "Today",
  week: "This week",
  month: "This month",
  year: "This year",
};

export function FilterDrawer({
  open,
  model,
  fields,
  filters,
  onClose,
  onApply,
}: {
  open: boolean;
  model: ModelSchema;
  fields: FieldSchema[];
  filters: Record<string, string>;
  onClose: () => void;
  onApply: (filters: Record<string, string>) => void;
}) {
  const [draft, setDraft] = useState(filters);
  const [rows, setRows] = useState<string[]>([]);
  const [described, setDescribed] = useState<ListFilter[]>([]);

  useEffect(() => {
    if (!open) return;
    setDraft(filters);
    const active = Object.keys(filters);
    setRows(active.length ? active : fields[0] ? [fields[0].name] : []);
  }, [open, filters, fields]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    listFilters(model.resource, filters)
      .then((next) => {
        if (!cancelled) setDescribed(next);
      })
      .catch(() => {
        if (!cancelled) setDescribed([]);
      });
    return () => {
      cancelled = true;
    };
  }, [open, model.resource, filters]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const setField = (name: string, value: string) => {
    setDraft((current) => ({ ...current, [name]: value }));
  };
  const byName = new Map(described.map((item) => [item.name, item]));
  const fieldByName = new Map(fields.map((field) => [field.name, field]));
  const unused = fields.filter((field) => !rows.includes(field.name));
  const chooseRow = (index: number, name: string) => {
    setRows((current) => current.map((item, itemIndex) => (itemIndex === index ? name : item)));
    setDraft((current) => {
      const next = { ...current };
      delete next[rows[index] ?? ""];
      return next;
    });
  };
  const removeRow = (index: number) => {
    const name = rows[index];
    setRows((current) => current.filter((_, itemIndex) => itemIndex !== index));
    if (name) setDraft((current) => {
      const next = { ...current };
      delete next[name];
      return next;
    });
  };

  return (
    <div className="fixed inset-0 z-40">
      <button type="button" className="absolute inset-0 bg-[#1a1a18]/40" aria-label="Close filters" onClick={onClose} />
      <aside
        role="dialog"
        aria-label="Filters"
        className="absolute inset-y-0 end-0 flex w-[min(100%,22rem)] flex-col border-s border-border bg-card shadow-float"
      >
        <header className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="text-[15px] font-semibold tracking-tight">Filters</h2>
          <button type="button" className="text-label text-muted-foreground hover:text-foreground" onClick={onClose}>
            Close
          </button>
        </header>
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-auto px-4 py-4">
          {rows.map((name, index) => {
            const field = fieldByName.get(name);
            if (!field) return null;
            const choices = fields.filter((item) => item.name === name || !rows.includes(item.name));
            return (
              <div key={`${name}-${index}`} className="flex flex-col gap-2 rounded-box border border-line p-3">
                <div className="flex items-center gap-2">
                  <Label htmlFor={`filter-key-${index}`} className="sr-only">Field</Label>
                  <select
                    id={`filter-key-${index}`}
                    aria-label="Field"
                    value={name}
                    onChange={(event) => chooseRow(index, event.target.value)}
                    className="h-8 min-w-0 flex-1 rounded-field border border-field-border bg-field px-2 text-label"
                  >
                    {choices.map((item) => (
                      <option key={item.name} value={item.name}>{item.label}</option>
                    ))}
                  </select>
                  <button type="button" className="text-note text-muted-foreground hover:text-foreground" onClick={() => removeRow(index)}>
                    Remove
                  </button>
                </div>
                <FilterField
                  model={model}
                  field={field}
                  described={byName.get(field.name)}
                  value={draft[field.name] ?? ""}
                  onChange={(value) => setField(field.name, value)}
                />
              </div>
            );
          })}
          {unused.length ? (
            <button
              type="button"
              className="self-start text-label font-medium text-link hover:underline"
              onClick={() => setRows((current) => [...current, unused[0].name])}
            >
              Add filter
            </button>
          ) : null}
        </div>
        <footer className="flex items-center justify-between gap-2 border-t border-line px-4 py-3">
          <Button type="button" variant="ghost" size="sm" onClick={() => setDraft({})}>
            Clear
          </Button>
          <div className="flex gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={() => {
                const next: Record<string, string> = {};
                for (const [key, value] of Object.entries(draft)) {
                  if (value) next[key] = value;
                }
                onApply(next);
              }}
            >
              Apply
            </Button>
          </div>
        </footer>
      </aside>
    </div>
  );
}

function selectedValues(value: string): string[] {
  return value ? value.split(",").filter(Boolean) : [];
}

function FilterField({
  model,
  field,
  described,
  value,
  onChange,
}: {
  model: ModelSchema;
  field: FieldSchema;
  described?: ListFilter;
  value: string;
  onChange: (value: string) => void;
}) {
  const kind = described?.kind ?? (field.reference ? "relation" : "exact");
  const [options, setOptions] = useState<{ value: string; label: string }[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (kind !== "relation") return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      fieldChoices(model.resource, field.name, query)
        .then((next) => {
          if (!cancelled) setOptions(next.map((choice) => ({ value: String(choice.value), label: choice.label })));
        })
        .catch(() => {
          if (!cancelled) setOptions([]);
        });
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [kind, model.resource, field.name, query]);

  if (kind === "choice" || kind === "boolean") {
    const choices = described?.options ?? [];
    const selected = new Set(selectedValues(value));
    const toggle = (option: string) => {
      const next = new Set(selected);
      if (next.has(option)) next.delete(option);
      else next.add(option);
      onChange([...next].join(","));
    };
    return (
      <fieldset className="flex flex-col gap-1.5">
        <legend className="text-label font-medium">{field.label}</legend>
        {choices.map((option) => (
          <label key={option.value} className="flex items-center gap-2 text-label">
            <input
              type={kind === "boolean" ? "radio" : "checkbox"}
              name={kind === "boolean" ? field.name : undefined}
              checked={selected.has(option.value)}
              onChange={() => (kind === "boolean" ? onChange(selected.has(option.value) ? "" : option.value) : toggle(option.value))}
            />
            <span className="flex-1">{option.label}</span>
            {option.count != null ? <span className="text-note text-muted-foreground tabular-nums">{option.count}</span> : null}
          </label>
        ))}
      </fieldset>
    );
  }

  if (kind === "number" || kind === "date") {
    const [start = "", end = ""] = value.split(",");
    const shortcut = described?.shortcuts?.includes(value) ? value : "";
    const write = (nextStart: string, nextEnd: string) => {
      onChange(nextStart || nextEnd ? `${nextStart},${nextEnd}` : "");
    };
    return (
      <div className="flex flex-col gap-1.5">
        <Label>{field.label}</Label>
        {kind === "date" ? (
          <div className="flex flex-wrap gap-1.5">
            {(described?.shortcuts ?? []).map((name) => (
              <button
                key={name}
                type="button"
                className={`h-7 rounded-full border px-2.5 text-note ${shortcut === name ? "border-primary bg-selected" : "border-line"}`}
                onClick={() => onChange(shortcut === name ? "" : name)}
              >
                {SHORTCUT_LABEL[name] ?? name}
              </button>
            ))}
          </div>
        ) : null}
        <div className="grid grid-cols-2 gap-2">
          <Input
            type={kind === "date" ? "date" : "number"}
            value={shortcut ? "" : start}
            aria-label={`${field.label} from`}
            placeholder="From"
            onChange={(event) => write(event.target.value, shortcut ? "" : end)}
          />
          <Input
            type={kind === "date" ? "date" : "number"}
            value={shortcut ? "" : end}
            aria-label={`${field.label} to`}
            placeholder="To"
            onChange={(event) => write(shortcut ? "" : start, event.target.value)}
          />
        </div>
      </div>
    );
  }

  if (kind === "relation") {
    const selected = new Set(selectedValues(value));
    return (
      <fieldset className="flex flex-col gap-1.5">
        <legend className="text-label font-medium">{field.label}</legend>
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Find a ${field.label.toLowerCase()}`}
          aria-label={`Find a ${field.label}`}
        />
        <div className="flex max-h-40 flex-col gap-1 overflow-auto">
          {options.map((option) => (
            <label key={option.value} className="flex items-center gap-2 text-label">
              <input
                type="checkbox"
                checked={selected.has(option.value)}
                onChange={() => {
                  const next = new Set(selected);
                  if (next.has(option.value)) next.delete(option.value);
                  else next.add(option.value);
                  onChange([...next].join(","));
                }}
              />
              <span className="truncate">{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={`filter-${field.name}`}>{field.label}</Label>
      <Input
        id={`filter-${field.name}`}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={kind === "text" ? `Contains ${field.label.toLowerCase()}` : field.label}
      />
    </div>
  );
}

export function filterLabel(field: FieldSchema, value: string, described?: ListFilter): string {
  if (described?.shortcuts?.includes(value)) return SHORTCUT_LABEL[value] ?? value;
  if ((described?.kind === "number" || described?.kind === "date" || field.type.includes("Date") || field.type.includes("Integer") || field.type.includes("Float") || field.type.includes("Decimal")) && value.includes(",")) {
    const [start, end] = value.split(",");
    if (start && end) return `${start}–${end}`;
    if (start) return `from ${start}`;
    if (end) return `to ${end}`;
  }
  const parts = value.split(",").filter(Boolean);
  const labels = parts.map((part) => {
    const choice = described?.options?.find((item) => item.value === part) ?? field.choices?.find((item) => String(item.value) === part);
    return choice ? choice.label : part;
  });
  return labels.join(", ") || value;
}
