import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { FieldSchema, ModelSchema } from "../api";
import { useAdmin } from "../admin-state";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ConfirmDialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Textarea } from "../components/ui/textarea";
import { ApiError, createRecord, deleteRecord, fieldChoices, getRecord, updateRecord, type Choice } from "../lib/client";
import { fieldShown, initials, isUserModel, toneFor } from "../lib/format";

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
  resource,
  field,
  value,
  disabled,
  onChange,
}: {
  resource: string;
  field: FieldSchema;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  const [q, setQ] = useState("");
  const [options, setOptions] = useState<Choice[]>([]);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      fieldChoices(resource, field.name, q)
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
  }, [resource, field.name, q]);

  const known = options.some((option) => String(option.value) === value);
  return (
    <div className="flex flex-col gap-2">
      <Input
        type="search"
        value={q}
        disabled={disabled}
        placeholder="Search…"
        aria-label={`Search ${field.label}`}
        onChange={(event) => setQ(event.target.value)}
      />
      <select
        className="h-9 w-full rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{field.required ? "Select…" : "None"}</option>
        {!known && value ? <option value={value}>{value}</option> : null}
        {options.map((option) => (
          <option key={String(option.value)} value={String(option.value)}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function FieldControl({
  model,
  field,
  value,
  disabled,
  error,
  onChange,
}: {
  model: ModelSchema;
  field: FieldSchema;
  value: unknown;
  disabled: boolean;
  error?: string;
  onChange: (value: unknown) => void;
}) {
  const text = value == null ? "" : String(value);
  const locked = disabled || Boolean(field.readOnly) || Boolean(field.primaryKey) || field.editable === false;

  let control;
  if (field.many && field.editable === false) {
    control = <p className="text-sm text-muted-foreground">{text || "—"}</p>;
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
        resource={model.resource}
        field={field}
        value={text}
        disabled={locked}
        onChange={onChange}
      />
    );
  } else if (field.choices?.length) {
    control = (
      <select
        className="h-9 w-full rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
        value={text}
        disabled={locked}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{field.required ? "Select…" : "None"}</option>
        {field.choices.map((choice) => (
          <option key={String(choice.value)} value={String(choice.value)}>
            {choice.label}
          </option>
        ))}
      </select>
    );
  } else if (field.type === "BooleanField") {
    control = (
      <div className="flex items-center justify-between rounded-lg border border-input px-3 py-2">
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
        <h3 className="font-display text-xl font-semibold">{name}</h3>
        <p className="text-sm text-muted-foreground">
          {username ? `@${username}` : ""}
          {username && record.email ? " · " : ""}
          {String(record.email ?? "")}
        </p>
        <Badge className={active ? "mt-2 bg-[#0F9F6E] text-white" : "mt-2"}>{active ? "Active" : "Inactive"}</Badge>
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
    <form className="mt-4 flex flex-col gap-3 rounded-xl border border-border bg-card p-4" onSubmit={(event) => void submit(event)}>
      <h3 className="font-display text-base font-semibold">Change password</h3>
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
  const omitPrimaryKey = userModel && !isCreate;

  const [values, setValues] = useState<Record<string, unknown>>({});
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState(!isCreate);
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
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
    return <p className="p-6 text-sm text-muted-foreground">This model is not in the admin.</p>;
  }

  const editable = isCreate ? model.permissions.create : model.permissions.edit;
  const fields = model.fields.filter((field) => fieldShown(field, isCreate, omitPrimaryKey));

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

  return (
    <div className="flex flex-col gap-5 p-6">
      <div>
        <Link to={`/${model.resource}`} className="text-sm text-muted-foreground hover:text-foreground">
          ← {model.labelPlural}
        </Link>
        <h2 className="mt-1 font-display text-2xl font-semibold tracking-tight">
          {isCreate ? `Add ${model.label}` : model.label}
        </h2>
      </div>

      {pending ? <p className="text-sm text-muted-foreground">Loading…</p> : null}
      {formError ? (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm whitespace-pre-wrap text-destructive">
          {formError}
        </p>
      ) : null}
      {notice ? <p className="text-sm text-[#0F9F6E]">{notice}</p> : null}

      {!pending && userModel && !isCreate && record ? (
        <div className="rounded-xl border border-border bg-card p-4">
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

      {!pending ? (
        <form className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5" onSubmit={(event) => void submit(event)}>
          {fields.map((field) => (
            <FieldControl
              key={field.name}
              model={model}
              field={field}
              value={values[field.name]}
              disabled={!editable}
              error={fieldErrors[field.name]}
              onChange={(next) => setValues((current) => ({ ...current, [field.name]: next }))}
            />
          ))}
          <div className="flex flex-wrap gap-2 pt-2">
            {editable ? (
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save"}
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
  );
}
