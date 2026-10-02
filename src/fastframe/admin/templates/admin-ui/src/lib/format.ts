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

export function formatCell(record: Record<string, unknown>, fieldName: string, model: ModelSchema): string {
  const field = model.fields.find((item) => item.name === fieldName);
  if (field?.relationshipName) {
    const related = record[field.relationshipName];
    if (related && typeof related === "object" && "display" in related) {
      return String((related as { display?: unknown }).display ?? "—");
    }
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
    const field = model.fields.find((item) => item.name === name);
    return {
      name,
      label: field?.label ?? name,
      sortable: !field?.relationshipName,
    };
  });
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
