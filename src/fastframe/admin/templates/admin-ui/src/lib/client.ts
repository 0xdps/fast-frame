import { API_URL } from "../api";

export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string>;

  constructor(message: string, status: number, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

interface Envelope<T> {
  data: T;
  total?: number;
}

export interface ListResult {
  data: Record<string, unknown>[];
  total: number;
}

export interface Choice {
  value: string | number;
  label: string;
}

async function http<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");

  const response = await fetch(url, { ...options, headers });
  const text = await response.text();
  let json: { detail?: unknown; data?: unknown } = {};
  if (text) {
    try {
      json = JSON.parse(text) as { detail?: unknown };
    } catch {
      json = {};
    }
  }

  if (!response.ok) {
    const parsed = parseError(json, response.statusText);
    throw new ApiError(parsed.message, response.status, parsed.fieldErrors);
  }
  return json as T;
}

function parseError(
  json: { detail?: unknown },
  fallback: string,
): { message: string; fieldErrors: Record<string, string> } {
  const detail = json.detail;
  if (Array.isArray(detail)) {
    const message = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) return String(item.msg);
        return String(item);
      })
      .join("\n");
    return { message: message || fallback, fieldErrors: {} };
  }
  if (detail && typeof detail === "object") {
    const record = detail as { errors?: Record<string, string>; message?: string };
    const fieldErrors = record.errors ?? {};
    const parts = Object.entries(fieldErrors).map(([field, message]) => `${field}: ${message}`);
    if (parts.length) return { message: parts.join("\n"), fieldErrors };
    if (record.message) return { message: String(record.message), fieldErrors };
  }
  if (typeof detail === "string" && detail) return { message: detail, fieldErrors: {} };
  return { message: fallback, fieldErrors: {} };
}

export async function listRecords(
  resource: string,
  params: {
    page: number;
    perPage: number;
    sortField: string;
    sortOrder: "ASC" | "DESC";
    q?: string;
    filters?: Record<string, string>;
  },
): Promise<ListResult> {
  const query = new URLSearchParams({
    page: String(params.page),
    perPage: String(params.perPage),
    sortField: params.sortField,
    sortOrder: params.sortOrder,
  });
  if (params.q) query.set("q", params.q);
  for (const [key, value] of Object.entries(params.filters ?? {})) {
    if (value) query.set(key, value);
  }
  const json = await http<Envelope<Record<string, unknown>[]>>(`${API_URL}/${resource}?${query}`);
  return { data: json.data, total: json.total ?? json.data.length };
}

export async function getRecord(resource: string, id: string): Promise<Record<string, unknown>> {
  const json = await http<Envelope<Record<string, unknown>>>(`${API_URL}/${resource}/${id}`);
  return json.data;
}

export async function createRecord(
  resource: string,
  data: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const json = await http<Envelope<Record<string, unknown>>>(`${API_URL}/${resource}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return json.data;
}

export async function updateRecord(
  resource: string,
  id: string,
  data: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const json = await http<Envelope<Record<string, unknown>>>(`${API_URL}/${resource}/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return json.data;
}

export async function deleteRecord(resource: string, id: string): Promise<void> {
  await http(`${API_URL}/${resource}/${id}`, { method: "DELETE" });
}

export async function deleteRecords(resource: string, ids: string[]): Promise<void> {
  const query = new URLSearchParams();
  for (const id of ids) query.append("ids", id);
  await http(`${API_URL}/${resource}?${query}`, { method: "DELETE" });
}

export async function fieldChoices(resource: string, field: string, q = ""): Promise<Choice[]> {
  const query = new URLSearchParams({ limit: "50" });
  if (q) query.set("q", q);
  const json = await http<Envelope<Choice[]>>(`${API_URL}/${resource}/choices/${field}?${query}`);
  return json.data;
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/logout`, { method: "POST" });
}
