import type { FieldSchema, ModelSchema } from "./api";
import { listColumns, sortFromOrdering } from "./lib/format";

export const PAGE_SIZE_OPTIONS = [25, 50, 100, 200];

const RESERVED = new Set(["q", "page", "perPage", "sort", "cols"]);

export interface ListQuery {
  q: string;
  page: number;
  perPage: number;
  sortField: string;
  sortOrder: "ASC" | "DESC";
  filters: Record<string, string>;
  columns: string[];
}

export function filterFields(model: ModelSchema): FieldSchema[] {
  return model.listFilter
    .map((name) => model.fields.find((field) => field.name === name))
    .filter((field): field is FieldSchema => Boolean(field));
}

export function readListQuery(search: string, model: ModelSchema): ListQuery {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const sort = sortFromOrdering(model.ordering);
  const requested = params.get("sort");
  let sortField = sort.field;
  let sortOrder = sort.order;
  if (requested) {
    sortOrder = requested.startsWith("-") ? "DESC" : "ASC";
    sortField = requested.replace(/^-/, "") || sort.field;
  }
  const page = Number(params.get("page"));
  const perPage = Number(params.get("perPage"));
  const available = listColumns(model).map((column) => column.name);
  const requestedColumns = (params.get("cols") ?? "")
    .split(",")
    .map((name) => name.trim())
    .filter((name) => available.includes(name));
  const filters: Record<string, string> = {};
  for (const field of filterFields(model)) {
    const values = params.getAll(field.name).flatMap((value) => value.split(",")).filter(Boolean);
    if (values.length) filters[field.name] = values.join(",");
  }
  return {
    q: params.get("q") ?? "",
    page: Number.isFinite(page) && page > 0 ? page : 1,
    perPage: PAGE_SIZE_OPTIONS.includes(perPage) ? perPage : model.listPerPage || 25,
    sortField,
    sortOrder,
    filters,
    columns: requestedColumns.length ? requestedColumns : available,
  };
}

export function writeListQuery(query: ListQuery, model: ModelSchema): string {
  const params = new URLSearchParams();
  const defaults = readListQuery("", model);
  if (query.q) params.set("q", query.q);
  if (query.page > 1) params.set("page", String(query.page));
  if (query.perPage !== defaults.perPage) params.set("perPage", String(query.perPage));
  const sort = query.sortOrder === "DESC" ? `-${query.sortField}` : query.sortField;
  const defaultSort = defaults.sortOrder === "DESC" ? `-${defaults.sortField}` : defaults.sortField;
  if (sort !== defaultSort) params.set("sort", sort);
  const available = listColumns(model).map((column) => column.name);
  if (query.columns.length && query.columns.join(",") !== available.join(",")) {
    params.set("cols", query.columns.join(","));
  }
  for (const [key, value] of Object.entries(query.filters)) {
    if (!value || RESERVED.has(key)) continue;
    for (const part of value.split(",")) {
      if (part) params.append(key, part);
    }
  }
  const text = params.toString();
  return text ? `?${text}` : "";
}
