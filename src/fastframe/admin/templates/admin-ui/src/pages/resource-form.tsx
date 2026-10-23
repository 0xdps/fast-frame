import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { FieldSchema, ModelSchema } from "../api";
import { useAdmin } from "../admin-state";
import { PageFrame } from "../components/page-frame";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ConfirmDialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { SelectField, type SelectOption } from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { Textarea } from "../components/ui/textarea";
import { ApiError, createRecord, deleteRecord, fieldChoices, getRecord, listRecords, updateRecord, type Choice } from "../lib/client";
import { fieldShown, initials, isUserModel, recordTitle, relatedObjects, relativeTime, resourceForReference, toneFor } from "../lib/format";

function createDefaults(model: ModelSchema): Record<string, unknown> {
  const values: Record<string, unknown> = {};
  for (const field of model.fields) {
    if (!fieldShown(field, true, false)) continue;
    if (field.type === "BooleanField") {
      values[field.name] = Boolean(field.default);
      continue;
    }
    if (field.type === "JSONField") {
      values[field.name] = JSON.stringify(field.default ?? {}, null, 2);
      continue;
    }
    if (field.default !== undefined && field.default !== null) {
      values[field.name] = field.default;
      continue;
    }
    values[field.name] = "";
  }
  return values;
}

function valuesFromRecord(model: ModelSchema, record: Record<string, unknown>): Record<string, unknown> {
  const values: Record<string, unknown> = {};
  for (const field of model.fields) {
    if (!fieldShown(field, false, false)) continue;
    const raw = record[field.name];
    if (field.type === "BooleanField") {
      values[field.name] = Boolean(raw);
    } else if (field.type === "JSONField") {
      values[field.name] = typeof raw === "string" ? raw : JSON.stringify(raw ?? {}, null, 2);
    } else if (field.type === "DateTimeField" && typeof raw === "string") {
      values[field.name] = raw.slice(0, 16);
    } else if (field.type === "DateField" && typeof raw === "string") {
      values[field.name] = raw.slice(0, 10);
    } else if (Array.isArray(raw)) {
      values[field.name] = raw.map(String).join(", ");
    } else if (raw == null) {
      values[field.name] = "";
    } else if (typeof raw === "object") {
      values[field.name] = "";
    } else {
      values[field.name] = raw;
    }
  }
  return values;
}

const EMPTY_AS_NULL = new Set([
  "IntegerField",
  "BigIntegerField",
  "FloatField",
  "DecimalField",
  "DateField",
  "DateTimeField",
  "ForeignKey",
]);

function coerceField(field: FieldSchema, raw: unknown): unknown {
  if (field.type === "BooleanField") return Boolean(raw);
  if (field.type === "JSONField") {
    if (typeof raw !== "string") return raw ?? {};
    if (raw.trim() === "") return {};
    return JSON.parse(raw) as unknown;
  }
  if (raw === "" || raw == null) {
    // Blank char fields are NOT NULL; only numbers, dates, and relations clear to null.
    return field.reference || EMPTY_AS_NULL.has(field.type) ? null : "";
  }
  if (field.type === "IntegerField" || field.type === "BigIntegerField") return Number.parseInt(String(raw), 10);
  if (field.type === "FloatField" || field.type === "DecimalField") return String(raw);
  if (field.choices?.length) {
    const match = field.choices.find((choice) => String(choice.value) === String(raw));
    return match ? match.value : raw;
  }
  if (field.reference) {
    const asNumber = Number(raw);
    if (String(asNumber) === String(raw).trim() && Number.isFinite(asNumber)) return asNumber;
  }
  return raw;
}

function buildPayload(model: ModelSchema, values: Record<string, unknown>, isCreate: boolean): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  for (const field of model.fields) {
    if (!fieldShown(field, isCreate, false)) continue;
    if (field.primaryKey || field.readOnly) continue;
    if (field.many && field.editable === false) continue;
    payload[field.name] = coerceField(field, values[field.name]);
  }
  return payload;
}

function ReferenceInput({
  model,
  models,
  field,
  value,
  record,
  disabled,
  onChange,
}: {
  model: ModelSchema;
  models: ModelSchema[];
  field: FieldSchema;
  value: string;
  record: Record<string, unknown> | null;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  const [q, setQ] = useState("");
  const [options, setOptions] = useState<Choice[]>([]);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      fieldChoices(model.resource, field.name, q)
        .then((next) => {
          if (!cancelled) setOptions(next);
        })
        .catch(() => {
          if (!cancelled) setOptions([]);
        });
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [model.resource, field.name, q]);

  const known = options.some((option) => String(option.value) === value);
  const knownLabel = options.find((option) => String(option.value) === value)?.label;
  const fromRecord = record ? relatedObjects(record, field).find((item) => item.id === value) : undefined;
  const label = knownLabel || fromRecord?.label;
  const target = resourceForReference(models, field.reference, model);
  const choices: SelectOption[] = [
    ...(q ? [] : [{ value: "", label: field.required ? "Select…" : "None" }]),
    ...(!q && !known && value ? [{ value, label: label || `#${value}` }] : []),
    ...options.map((option) => ({ value: String(option.value), label: option.label })),
  ];
  return (
    <div className="flex flex-col gap-2">
      <SelectField
        ariaLabel={field.label}
        value={value}
        options={choices}
        disabled={disabled}
        searchable
        query={q}
        onQueryChange={setQ}
        onChange={onChange}
      />
      {value && target && label ? (
        <Link to={`/${target}/${value}`} className="text-sm font-medium text-primary hover:underline">
          {label}
        </Link>
      ) : null}
    </div>
  );
}

function RelatedLinks({
  model,
  models,
  field,
  record,
}: {
  model: ModelSchema;
  models: ModelSchema[];
  field: FieldSchema;
  record: Record<string, unknown> | null;
}) {
  const related = record ? relatedObjects(record, field) : [];
  const [labels, setLabels] = useState<Record<string, string>>({});
  const unresolved = field.many && related.some((item) => item.label === `#${item.id}`);

  useEffect(() => {
    if (!unresolved) return;
    let cancelled = false;
    fieldChoices(model.resource, field.name)
      .then((options) => {
        if (cancelled) return;
        const next: Record<string, string> = {};
        for (const option of options) next[String(option.value)] = option.label;
        setLabels(next);
      })
      .catch(() => {
        if (!cancelled) setLabels({});
      });
    return () => {
      cancelled = true;
    };
  }, [unresolved, model.resource, field.name]);

  if (!related.length) return <p className="text-sm text-muted-foreground">—</p>;
  const target = resourceForReference(models, field.reference, model);
  return (
    <p className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
      {related.map((item) => {
        const label = labels[item.id] || item.label;
        if (!target) return <span key={item.id}>{label}</span>;
        return (
          <Link key={item.id} to={`/${target}/${item.id}`} className="font-medium text-primary hover:underline">
            {label}
          </Link>
        );
      })}
    </p>
  );
}

function FieldControl({
  model,
  models,
  field,
  value,
  record,
  viewing,
  disabled,
  error,
  onChange,
}: {
  model: ModelSchema;
  models: ModelSchema[];
  field: FieldSchema;
  value: unknown;
  record: Record<string, unknown> | null;
  viewing: boolean;
  disabled: boolean;
  error?: string;
  onChange: (value: unknown) => void;
}) {
  const text = value == null ? "" : String(value);
  const locked = viewing || disabled || Boolean(field.readOnly) || Boolean(field.primaryKey) || field.editable === false;

  let control;
  if (field.many && field.editable === false) {
    control = (
      <div className="flex min-h-9 flex-wrap items-center rounded-lg border border-input bg-muted px-3 py-1.5">
        <RelatedLinks model={model} models={models} field={field} record={record} />
      </div>
    );
  } else if (field.writeOnly) {
    control = (
      <Input
        type="password"
        autoComplete="new-password"
        value={text}
        disabled={locked}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  } else if (field.reference && !field.many) {
    control = (
      <ReferenceInput
        model={model}
        models={models}
        field={field}
        value={text}
        record={record}
        disabled={locked}
        onChange={onChange}
      />
    );
  } else if (field.choices?.length) {
    control = (
      <SelectField
        ariaLabel={field.label}
        value={text}
        disabled={locked}
        onChange={(next) => onChange(next)}
        options={[
          { value: "", label: field.required ? "Select…" : "None" },
          ...field.choices.map((choice) => ({ value: String(choice.value), label: choice.label })),
        ]}
      />
    );
  } else if (field.type === "BooleanField") {
    control = (
      <div className={`flex items-center justify-between rounded-lg border border-input px-3 py-2 ${locked ? "bg-muted" : ""}`}>
        <span className="text-sm text-muted-foreground">{value ? "Yes" : "No"}</span>
        <Switch checked={Boolean(value)} disabled={locked} onCheckedChange={onChange} aria-label={field.label} />
      </div>
    );
  } else if (field.type === "TextField" || field.type === "JSONField") {
    control = (
      <Textarea
        value={text}
        rows={field.type === "JSONField" ? 8 : 4}
        disabled={locked}
        className={field.type === "JSONField" ? "font-mono text-xs" : undefined}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  } else if (field.type === "IntegerField" || field.type === "BigIntegerField" || field.type === "FloatField" || field.type === "DecimalField") {
    control = (
      <Input
        type="number"
        value={text}
        disabled={locked}
        step={field.type === "IntegerField" || field.type === "BigIntegerField" ? 1 : "any"}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  } else if (field.type === "DateField") {
    control = <Input type="date" value={text} disabled={locked} onChange={(event) => onChange(event.target.value)} />;
  } else if (field.type === "DateTimeField") {
    control = (
      <Input type="datetime-local" value={text} disabled={locked} onChange={(event) => onChange(event.target.value)} />
    );
  } else {
    control = (
      <Input
        type={field.name === "email" || field.type === "EmailField" ? "email" : "text"}
        value={text}
        disabled={locked}
        maxLength={field.maxLength}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={field.name}>{field.label}</Label>
      <div id={field.name}>{control}</div>
      {field.helpText ? <p className="text-xs text-muted-foreground">{field.helpText}</p> : null}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

const ACTION_LABEL: Record<string, string> = {
  create: "Created",
  update: "Changed",
  delete: "Deleted",
};

function formatChange(value: unknown): string {
  if (value == null || value === "") return "empty";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function HistoryPanel({ modelName, objectId }: { modelName: string; objectId: string }) {
  const [rows, setRows] = useState<Record<string, unknown>[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listRecords("auditlog", {
      page: 1,
      perPage: 100,
      sortField: "created_at",
      sortOrder: "DESC",
      filters: { model_name: modelName, object_id: objectId },
    })
      .then((result) => {
        if (cancelled) return;
        setRows(result.data);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load history.");
      });
    return () => {
      cancelled = true;
    };
  }, [modelName, objectId]);

  if (error) return <p className="text-label text-muted-foreground">{error}</p>;
  if (!rows) return <p className="text-label text-muted-foreground">Loading history…</p>;
  if (!rows.length) return <p className="text-label text-muted-foreground">No changes recorded for this record.</p>;

  return (
    <ol className="flex flex-col">
      {rows.map((row) => {
        const action = String(row.action ?? "");
        const changes = row.changes;
        const fields =
          changes && typeof changes === "object" && !Array.isArray(changes) && "fields" in changes
            ? null
            : changes && typeof changes === "object" && !Array.isArray(changes)
              ? Object.entries(changes as Record<string, { old?: unknown; new?: unknown }>)
              : null;
        return (
          <li key={String(row.id)} className="border-b border-line py-3 last:border-b-0">
            <p className="text-label">
              <span className="font-medium">{ACTION_LABEL[action] ?? action}</span>
              <span className="text-muted-foreground"> by {String(row.username || "System")}</span>
            </p>
            <p className="text-note text-muted-foreground">{relativeTime(String(row.created_at ?? ""))}</p>
            {fields?.length ? (
              <ul className="mt-2 flex flex-col gap-1">
                {fields.map(([name, pair]) => (
                  <li key={name} className="text-label text-muted-foreground">
                    <span className="font-medium text-foreground">{name.replaceAll("_", " ")}</span>
                    {": "}
                    {formatChange(pair?.old)} → {formatChange(pair?.new)}
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

function UserIdentity({ record }: { record: Record<string, unknown> }) {
  const first = String(record.first_name ?? "");
  const last = String(record.last_name ?? "");
  const username = String(record.username ?? "");
  const name = [first, last].filter(Boolean).join(" ") || username || "User";
  const active = Boolean(record.is_active);
  return (
    <div className="flex items-center gap-4">
      <span
        className="grid size-14 place-items-center rounded-full text-lg font-semibold text-white"
        style={{ background: toneFor(username || name) }}
        aria-hidden="true"
      >
        {initials(first, last, username)}
      </span>
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{name}</h2>
        <p className="text-sm text-muted-foreground">
          {username ? `@${username}` : ""}
          {username && record.email ? " · " : ""}
          {String(record.email ?? "")}
        </p>
        <Badge className={active ? "tone-2 mt-2" : "mt-2"}>{active ? "Active" : "Inactive"}</Badge>
      </div>
    </div>
  );
}

function ChangePassword({ resource, id, onDone }: { resource: string; id: string; onDone: () => void }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!password) {
      setError("Enter a new password.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      await updateRecord(resource, id, { password });
      setPassword("");
      setConfirm("");
      onDone();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not change the password.");
    } finally {
      setPending(false);
    }
  };

  return (
    <form className="mt-4 flex flex-col gap-3 rounded-box border border-border bg-subtle p-4" onSubmit={(event) => void submit(event)}>
      <h3 className="text-label font-semibold">Change password</h3>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="new-password">New password</Label>
        <Input id="new-password" type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="confirm-password">Confirm password</Label>
        <Input
          id="confirm-password"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
        />
      </div>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          Save password
        </Button>
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

export function ResourceForm({ mode }: { mode: "create" | "edit" }) {
  const { resource = "", id = "" } = useParams();
  const { models, refreshKey } = useAdmin();
  const model = models.find((item) => item.resource === resource);
  const navigate = useNavigate();
  const isCreate = mode === "create";
  const userModel = model ? isUserModel(model) : false;

  const [values, setValues] = useState<Record<string, unknown>>({});
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState(!isCreate);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(isCreate);
  const [changingPassword, setChangingPassword] = useState(false);
  const [tab, setTab] = useState<"details" | "history">("details");
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const formKey = `${resource}:${isCreate ? "new" : id}:${isCreate ? 0 : refreshKey}`;
  const [seen, setSeen] = useState<string | null>(null);

  if (model && seen !== formKey) {
    setSeen(formKey);
    setFieldErrors({});
    setFormError(null);
    setNotice(null);
    setChangingPassword(false);
    setTab("details");
    setEditing(isCreate);
    if (isCreate) {
      setValues(createDefaults(model));
      setRecord(null);
      setPending(false);
    } else {
      setPending(true);
    }
  }

  useEffect(() => {
    if (!model || isCreate || !id) return;
    let cancelled = false;
    getRecord(model.resource, id)
      .then((loaded) => {
        if (cancelled) return;
        setRecord(loaded);
        setValues(valuesFromRecord(model, loaded));
      })
      .catch((err: unknown) => {
        if (!cancelled) setFormError(err instanceof Error ? err.message : "Could not load this record.");
      })
      .finally(() => {
        if (!cancelled) setPending(false);
      });
    return () => {
      cancelled = true;
    };
  }, [model, isCreate, id, refreshKey]);

  if (!model) {
    return (
      <PageFrame title="Not found">
        <p className="px-4 py-6 text-label text-muted-foreground lg:px-7">This model is not in the admin.</p>
      </PageFrame>
    );
  }

  const editable = isCreate ? model.permissions.create : model.permissions.edit;
  const viewing = !isCreate && !editing;
  const fields = model.fields
    .filter((field) => fieldShown(field, isCreate, false))
    .toSorted((a, b) => Number(b.primaryKey) - Number(a.primaryKey));

  const cancelEdit = () => {
    if (record) setValues(valuesFromRecord(model, record));
    setFieldErrors({});
    setFormError(null);
    setNotice(null);
    setEditing(false);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!editable) return;
    const nextErrors: Record<string, string> = {};
    for (const field of fields) {
      if (field.readOnly || field.primaryKey || (field.many && field.editable === false)) continue;
      if (!field.required) continue;
      const raw = values[field.name];
      if (field.type === "BooleanField") continue;
      if (raw === "" || raw == null) nextErrors[field.name] = "This field is required.";
    }
    if (Object.keys(nextErrors).length) {
      setFieldErrors(nextErrors);
      setFormError(null);
      return;
    }
    setSaving(true);
    setFieldErrors({});
    setFormError(null);
    setNotice(null);
    try {
      const payload = buildPayload(model, values, isCreate);
      if (isCreate) {
        const created = await createRecord(model.resource, payload);
        const createdId = created.id ?? created[model.pkField];
        navigate(createdId == null ? `/${model.resource}` : `/${model.resource}/${createdId}`);
      } else {
        const updated = await updateRecord(model.resource, id, payload);
        setRecord(updated);
        setValues(valuesFromRecord(model, updated));
        setEditing(false);
        setNotice("Saved.");
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setFieldErrors(err.fieldErrors);
        setFormError(err.message);
      } else if (err instanceof SyntaxError) {
        setFormError("One of the JSON fields is not valid JSON.");
      } else {
        setFormError(err instanceof Error ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setDeleting(true);
    try {
      await deleteRecord(model.resource, id);
      navigate(`/${model.resource}`);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Could not delete this record.");
      setConfirmingDelete(false);
    } finally {
      setDeleting(false);
    }
  };

  const heading = isCreate ? `New ${model.label}` : recordTitle(record, model, model.label);
  const audit = models.find((item) => item.resource === "auditlog");
  const showHistory = !isCreate && Boolean(audit?.permissions.view);

  return (
    <PageFrame
      title={heading}
      breadcrumb={
        <>
          <Link to={`/${model.resource}`} className="hover:text-foreground">
            {model.labelPlural}
          </Link>
          <span aria-hidden="true">/</span>
          {isCreate ? null : (
            <>
              <span>{model.label}</span>
              <span aria-hidden="true">/</span>
            </>
          )}
          <span aria-current="page" className="truncate text-foreground">
            {heading}
          </span>
        </>
      }
      messages={
        formError || notice ? (
          <>
            {formError ? (
              <p className="rounded-box border border-destructive/30 bg-destructive/10 px-3 py-2 text-label whitespace-pre-wrap text-destructive">
                {formError}
              </p>
            ) : null}
            {notice ? (
              <p className="rounded-box border border-primary/30 bg-selected px-3 py-2 text-label text-foreground">{notice}</p>
            ) : null}
          </>
        ) : null
      }
    >
    <div className="flex flex-1 flex-col gap-5 bg-background px-4 pt-6 lg:px-7">
      {pending ? <p className="text-label text-muted-foreground">Loading…</p> : null}

      {!pending && userModel && !isCreate && record ? (
        <div className="rounded-box border border-border bg-card p-5 shadow-quiet">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <UserIdentity record={record} />
            <Button type="button" variant="outline" onClick={() => setChangingPassword((open) => !open)}>
              {changingPassword ? "Close" : "Change password"}
            </Button>
          </div>
          {changingPassword ? (
            <ChangePassword
              resource={model.resource}
              id={id}
              onDone={() => {
                setChangingPassword(false);
                setNotice("Password changed.");
              }}
            />
          ) : null}
        </div>
      ) : null}

      {showHistory ? (
        <div role="tablist" aria-label="Record" className="flex gap-1">
          {(["details", "history"] as const).map((name) => (
            <button
              key={name}
              type="button"
              role="tab"
              aria-selected={tab === name}
              className={`h-8 rounded-field px-3 text-label font-medium ${
                tab === name ? "bg-card text-foreground shadow-quiet" : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setTab(name)}
            >
              {name === "details" ? "Details" : "History"}
            </button>
          ))}
        </div>
      ) : null}

      {!pending && tab === "history" && showHistory ? (
        <section className="max-w-3xl rounded-box border border-border bg-card px-5 py-2 shadow-quiet">
          <HistoryPanel modelName={model.name} objectId={id} />
        </section>
      ) : null}

      {!pending && tab === "details" ? (
        <form className="flex max-w-3xl flex-col gap-5 rounded-box border border-border bg-card p-5 shadow-quiet" onSubmit={(event) => void submit(event)}>
          {fields.map((field) => (
            <FieldControl
              key={field.name}
              model={model}
              models={models}
              field={field}
              value={values[field.name]}
              record={record}
              viewing={viewing}
              disabled={!editable}
              error={fieldErrors[field.name]}
              onChange={(next) => setValues((current) => ({ ...current, [field.name]: next }))}
            />
          ))}
          <div className="flex flex-wrap gap-2 pt-2">
            {editable && viewing ? (
              <Button
                type="button"
                onClick={() => {
                  setNotice(null);
                  setEditing(true);
                }}
              >
                Edit
              </Button>
            ) : null}
            {editable && !viewing ? (
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </Button>
            ) : null}
            {editable && editing && !isCreate ? (
              <Button type="button" variant="outline" onClick={cancelEdit} disabled={saving}>
                Cancel
              </Button>
            ) : null}
            {!isCreate && model.permissions.delete ? (
              <Button type="button" variant="outline" onClick={() => setConfirmingDelete(true)}>
                Delete
              </Button>
            ) : null}
          </div>
        </form>
      ) : null}

      <ConfirmDialog
        open={confirmingDelete}
        title={`Delete this ${model.label}?`}
        description="This cannot be undone."
        confirmLabel="Delete"
        pending={deleting}
        onOpenChange={setConfirmingDelete}
        onConfirm={() => void remove()}
      />
    </div>
    </PageFrame>
  );
}
