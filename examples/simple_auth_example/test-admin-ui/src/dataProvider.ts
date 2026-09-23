import { HttpError, type DataProvider, type RaRecord } from "react-admin";

import { API_URL } from "./api";

interface Envelope<T> {
  data: T;
  total?: number;
}

function asRecord(row: Record<string, unknown>): RaRecord {
  return row as RaRecord;
}

async function http<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  const text = await response.text();
  const json = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new HttpError(errorMessage(json, response.statusText), response.status, json.detail ?? json);
  }
  return json as T;
}

function errorMessage(json: { detail?: unknown }, fallback: string): string {
  const detail = json.detail;
  if (detail && typeof detail === "object" && "errors" in detail) {
    const errors = (detail as { errors?: Record<string, string> }).errors ?? {};
    const parts = Object.entries(errors).map(([field, message]) => `${field}: ${message}`);
    if (parts.length) return parts.join("\n");
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: string }).message);
  }
  if (typeof detail === "string") return detail;
  return fallback;
}

export const dataProvider = {
  getList: async (resource, params) => {
    const { page, perPage } = params.pagination ?? { page: 1, perPage: 25 };
    const { field, order } = params.sort ?? { field: "id", order: "ASC" };
    const query = new URLSearchParams({
      page: String(page),
      perPage: String(perPage),
      sortField: field,
      sortOrder: order,
    });

    const { q, ...filters } = params.filter ?? {};
    if (q) query.set("q", String(q));
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, String(value));
      }
    }

    const json = await http<Envelope<Record<string, unknown>[]>>(
      `${API_URL}/${resource}?${query}`,
    );
    return { data: json.data.map(asRecord), total: json.total ?? json.data.length };
  },

  getOne: async (resource, params) => {
    const json = await http<Envelope<Record<string, unknown>>>(
      `${API_URL}/${resource}/${params.id}`,
    );
    return { data: asRecord(json.data) };
  },

  getMany: async (resource, params) => {
    const rows = await Promise.all(
      params.ids.map(async (id) => {
        const json = await http<Envelope<Record<string, unknown>>>(
          `${API_URL}/${resource}/${id}`,
        );
        return asRecord(json.data);
      }),
    );
    return { data: rows };
  },

  getManyReference: async (resource, params) => {
    return dataProvider.getList(resource, {
      ...params,
      filter: { ...params.filter, [params.target]: params.id },
    });
  },

  create: async (resource, params) => {
    const json = await http<Envelope<Record<string, unknown>>>(`${API_URL}/${resource}`, {
      method: "POST",
      body: JSON.stringify(params.data),
    });
    return { data: asRecord(json.data) };
  },

  update: async (resource, params) => {
    const json = await http<Envelope<Record<string, unknown>>>(
      `${API_URL}/${resource}/${params.id}`,
      { method: "PUT", body: JSON.stringify(params.data) },
    );
    return { data: asRecord(json.data) };
  },

  updateMany: async (resource, params) => {
    await Promise.all(
      params.ids.map((id) =>
        http(`${API_URL}/${resource}/${id}`, {
          method: "PUT",
          body: JSON.stringify(params.data),
        }),
      ),
    );
    return { data: params.ids };
  },

  delete: async (resource, params) => {
    const json = await http<Envelope<Record<string, unknown>>>(
      `${API_URL}/${resource}/${params.id}`,
      { method: "DELETE" },
    );
    return { data: asRecord(json.data) };
  },

  deleteMany: async (resource, params) => {
    const query = new URLSearchParams();
    for (const id of params.ids) query.append("ids", String(id));
    await http(`${API_URL}/${resource}?${query}`, { method: "DELETE" });
    return { data: params.ids };
  },
} as DataProvider;
