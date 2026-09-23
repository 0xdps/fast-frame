import { useState, type FormEvent } from "react";
import { Button } from "@mui/material";
import { Create, Edit, SimpleForm, useNotify, useRecordContext, useUpdate } from "react-admin";

import type { ModelSchema } from "./api";
import { formFields, buildResourceViews, type ResourceViews } from "./resources";

const tones = ["#3157E8", "#0F9F6E", "#6D5BD0", "#0E7490", "#C2410C"];

function toneFor(name: string): string {
  let index = 0;
  for (const char of name) index = (index + char.charCodeAt(0)) % tones.length;
  return tones[index] ?? tones[0];
}

function initials(first: unknown, last: unknown, username: unknown): string {
  const a = String(first ?? "").trim();
  const b = String(last ?? "").trim();
  if (a && b) return `${a[0]}${b[0]}`.toUpperCase();
  const fallback = a || b || String(username ?? "").trim();
  return (fallback.slice(0, 2) || "?").toUpperCase();
}

function createDefaults(model: ModelSchema): Record<string, unknown> {
  return Object.fromEntries(
    model.fields
      .filter((field) => !field.primaryKey && !field.writeOnly && field.default !== undefined)
      .map((field) => [field.name, field.default]),
  );
}

function UserIdentity() {
  const record = useRecordContext();
  if (!record) return null;
  const first = String(record.first_name ?? "");
  const last = String(record.last_name ?? "");
  const username = String(record.username ?? "");
  const name = [first, last].filter(Boolean).join(" ") || username || "User";
  const active = Boolean(record.is_active);
  return (
    <div className="profile-identity">
      <div className="avatar lg" style={{ background: toneFor(username || name) }} aria-hidden="true">
        {initials(first, last, username)}
      </div>
      <div>
        <h2>{name}</h2>
        <p className="user-email">
          {username ? `@${username}` : ""}
          {username && record.email ? " · " : ""}
          {String(record.email ?? "")}
        </p>
        <span className={active ? "pill on" : "pill off"}>{active ? "Active" : "Inactive"}</span>
      </div>
    </div>
  );
}

function ChangePassword({ resource, onDone }: { resource: string; onDone: () => void }) {
  const record = useRecordContext();
  const notify = useNotify();
  const [update, { isPending }] = useUpdate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!record) return;
    if (!password) {
      setError("Enter a new password.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setError(null);
    update(
      resource,
      { id: record.id, data: { password }, previousData: record },
      {
        onSuccess: () => {
          notify("Password changed");
          setPassword("");
          setConfirm("");
          onDone();
        },
        onError: (err: unknown) => {
          setError(err instanceof Error ? err.message : "Could not change the password.");
        },
      },
    );
  };

  return (
    <form className="password-panel" onSubmit={submit}>
      <h3>Change password</h3>
      <label>
        New password
        <input type="password" value={password} autoComplete="new-password" onChange={(event) => setPassword(event.target.value)} />
      </label>
      <label>
        Confirm password
        <input type="password" value={confirm} autoComplete="new-password" onChange={(event) => setConfirm(event.target.value)} />
      </label>
      {error ? <p className="password-error">{error}</p> : null}
      <div className="password-actions">
        <Button type="submit" variant="contained" disabled={isPending}>
          Save password
        </Button>
        <Button type="button" onClick={onDone}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

function UserProfile({ model, models }: { model: ModelSchema; models: ModelSchema[] }) {
  const [changingPassword, setChangingPassword] = useState(false);
  return (
    <div className="user-profile">
      <header className="profile-header">
        <UserIdentity />
        <Button variant="outlined" onClick={() => setChangingPassword((open) => !open)}>
          {changingPassword ? "Close" : "Change password"}
        </Button>
      </header>
      {changingPassword ? (
        <ChangePassword resource={model.resource} onDone={() => setChangingPassword(false)} />
      ) : null}
      <SimpleForm>{formFields(model, models, false, { omitPrimaryKey: true })}</SimpleForm>
    </div>
  );
}

export function isUserModel(model: ModelSchema): boolean {
  return model.name === "SimpleUser" || model.resource === "simpleuser";
}

export function buildUserViews(model: ModelSchema, models: ModelSchema[]): ResourceViews {
  const generic = buildResourceViews(model, models);

  const UserEdit = () => (
    <Edit className="user-edit" title="User">
      <UserProfile model={model} models={models} />
    </Edit>
  );

  const UserCreate = () => (
    <Create className="user-create" title="Add a user">
      <SimpleForm defaultValues={createDefaults(model)}>
        {formFields(model, models, true)}
      </SimpleForm>
    </Create>
  );

  return {
    ...generic,
    edit: model.permissions.edit ? UserEdit : undefined,
    create: model.permissions.create ? UserCreate : undefined,
    recordRepresentation: (record) => {
      const name = [record.first_name, record.last_name].filter(Boolean).join(" ");
      return String(name || record.username || record.id || "");
    },
  };
}
