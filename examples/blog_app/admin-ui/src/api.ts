/** FastFrame admin API base URL. Override with VITE_API_URL. */
export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000/api/admin";

export interface FieldChoice {
  value: string | number | boolean;
  label: string;
}

export interface FieldSchema {
  name: string;
  type: string;
  label: string;
  required: boolean;
  nullable: boolean;
  helpText: string;
  primaryKey: boolean;
  readOnly?: boolean;
  writeOnly?: boolean;
  maxLength?: number;
  choices?: FieldChoice[];
  reference?: string;
  relationshipName?: string | null;
  default?: unknown;
}

export interface ModelPermissions {
  create: boolean;
  edit: boolean;
  delete: boolean;
  view: boolean;
}

export interface ModelSchema {
  name: string;
  resource: string;
  label: string;
  labelPlural: string;
  appLabel: string;
  pkField: string;
  ordering: string[];
  fields: FieldSchema[];
  listDisplay: string[];
  searchFields: string[];
  listFilter: string[];
  listPerPage: number;
  permissions: ModelPermissions;
}

export interface SchemaResponse {
  models: ModelSchema[];
}
