import type { FieldSchema, ModelSchema } from "../api";

/** API datetimes are naive UTC. A bare timestamp would otherwise parse as local time. */
export function parseApiDate(iso: string): number {
  const hasOffset = /(Z|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(hasOffset ? iso : `${iso}Z`).getTime();
}

export function relativeTime(iso: string): string {
  const then = parseApiDate(iso);
  if (Number.isNaN(then)) return "";
  let diff = (then - Date.now()) / 1000;
  const divisions: [number, Intl.RelativeTimeFormatUnit][] = [
    [60, "seconds"],
    [60, "minutes"],
    [24, "hours"],
    [7, "days"],
    [4.345, "weeks"],
    [12, "months"],
    [Number.POSITIVE_INFINITY, "years"],
  ];
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  for (const [amount, unit] of divisions) {
    if (Math.abs(diff) < amount) return rtf.format(Math.round(diff), unit);
    diff /= amount;
  }
  return rtf.format(Math.round(diff), "years");
}

export function relationKey(field: FieldSchema): string {
  if (field.relationshipName) return field.relationshipName;
  if (field.name.endsWith("_id")) return field.name.slice(0, -3);
  return `${field.name}_rel`;
}

export function fieldForColumn(model: ModelSchema, name: string): FieldSchema | undefined {
  return (
    model.fields.find((field) => field.name === name) ??
    model.fields.find((field) => field.reference && relationKey(field) === name)
  );
}

export interface RelatedObject {
  id: string;
  label: string;
}

export function relatedObjects(record: Record<string, unknown>, field: FieldSchema): RelatedObject[] {
  if (field.many) {
    const raw = record[field.name];
    if (!Array.isArray(raw)) return [];
    return raw.flatMap((item) => {
      if (item && typeof item === "object" && "id" in item) {
        const related = item as { id?: unknown; display?: unknown };
        if (related.id == null || related.id === "") return [];
        const id = String(related.id);
        const label = related.display == null || related.display === "" ? `#${id}` : String(related.display);
        return [{ id, label }];
      }
      if (item == null || item === "") return [];
      const id = String(item);
      return [{ id, label: `#${id}` }];
    });
  }

  const nested = record[relationKey(field)];
  if (nested && typeof nested === "object" && !Array.isArray(nested) && "id" in nested) {
    const related = nested as { id?: unknown; display?: unknown };
    if (related.id == null || related.id === "") return [];
    const id = String(related.id);
    const label = related.display == null || related.display === "" ? `#${id}` : String(related.display);
    return [{ id, label }];
  }

  const raw = record[field.name];
  if (raw == null || raw === "") return [];
  const id = String(raw);
  return [{ id, label: `#${id}` }];
}

export function resourceForReference(
  models: ModelSchema[],
  reference: string | undefined,
  current: ModelSchema,
): string | undefined {
  if (!reference || reference === "self") return current.resource;
  const name = reference.includes(".") ? reference.slice(reference.lastIndexOf(".") + 1) : reference;
  return models.find((model) => model.name === name)?.resource;
}

export function formatCell(record: Record<string, unknown>, fieldName: string, model: ModelSchema): string {
  const field = fieldForColumn(model, fieldName);
  if (field?.reference) {
    const related = relatedObjects(record, field);
    return related.length ? related.map((item) => item.label).join(", ") : "—";
  }
  const value = record[fieldName];
  if (value == null || value === "") return "—";
  if (field?.type === "BooleanField") return value ? "Yes" : "No";
  if ((field?.type === "DateTimeField" || field?.type === "DateField") && typeof value === "string") {
    const then = parseApiDate(field.type === "DateField" ? `${value.slice(0, 10)}T00:00:00` : value);
    if (!Number.isNaN(then)) {
      return field.type === "DateField"
        ? new Date(then).toLocaleDateString()
        : new Date(then).toLocaleString();
    }
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function recordId(record: Record<string, unknown>, model: ModelSchema): string {
  const raw = record.id ?? record[model.pkField];
  return raw == null ? "" : String(raw);
}

export function sortFromOrdering(ordering: string[]): { field: string; order: "ASC" | "DESC" } {
  const first = ordering[0];
  if (!first) return { field: "id", order: "ASC" };
  if (first.startsWith("-")) return { field: first.slice(1), order: "DESC" };
  return { field: first, order: "ASC" };
}

export function listColumns(model: ModelSchema): { name: string; label: string; sortable: boolean }[] {
  const names = (model.listDisplay.length ? model.listDisplay : ["id"]).filter((name) => name !== "__str__");
  const columns = names.map((name) => {
    const field = fieldForColumn(model, name);
    const isColumn = model.fields.some((item) => item.name === name);
    return {
      name,
      label: field?.label ?? name,
      sortable: isColumn && !field?.many,
    };
  });
  const shown = new Set(columns.map((column) => column.name));
  for (const field of model.fields) {
    if (!field.reference || field.many || field.writeOnly) continue;
    if (shown.has(field.name) || shown.has(relationKey(field))) continue;
    columns.push({ name: field.name, label: field.label, sortable: true });
    shown.add(field.name);
  }
  return columns.length ? columns : [{ name: "id", label: "Id", sortable: true }];
}

export function isUserModel(model: ModelSchema): boolean {
  return (
    model.name === "User" ||
    model.name === "SimpleUser" ||
    model.resource === "user" ||
    model.resource === "simpleuser"
  );
}

const tones = ["#3157E8", "#0F9F6E", "#6D5BD0", "#0E7490", "#C2410C"];

export function toneFor(name: string): string {
  let index = 0;
  for (const char of name) index = (index + char.charCodeAt(0)) % tones.length;
  return tones[index] ?? tones[0];
}

export function initials(first: unknown, last: unknown, username: unknown): string {
  const a = String(first ?? "").trim();
  const b = String(last ?? "").trim();
  if (a && b) return `${a[0]}${b[0]}`.toUpperCase();
  const fallback = a || b || String(username ?? "").trim();
  return (fallback.slice(0, 2) || "?").toUpperCase();
}

export function fieldShown(field: FieldSchema, isCreate: boolean, omitPrimaryKey: boolean): boolean {
  if (field.writeOnly) return isCreate;
  if (field.primaryKey) return !isCreate && !omitPrimaryKey;
  if (field.readOnly && isCreate) return false;
  if (field.many && field.editable === false && isCreate) return false;
  return true;
}
