import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAdmin } from "../admin-state";
import { listRecords } from "../lib/client";
import { relativeTime } from "../lib/format";

const ACTION_LABEL: Record<string, string> = {
  create: "created",
  update: "updated",
  delete: "deleted",
};

const PREVIEW_SIZE = 5;

export function Overview() {
  const { models, refreshKey } = useAdmin();
  const audit = models.find((model) => model.resource === "auditlog");
  const canView = audit?.permissions.view ?? false;
  const [rows, setRows] = useState<Record<string, unknown>[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadedKey, setLoadedKey] = useState(-1);
  const pending = canView && loadedKey !== refreshKey;

  useEffect(() => {
    if (!canView) return;
    let cancelled = false;
    const key = refreshKey;
    listRecords("auditlog", { page: 1, perPage: PREVIEW_SIZE, sortField: "created_at", sortOrder: "DESC" })
      .then((result) => {
        if (cancelled) return;
        setRows(result.data);
        setError(null);
        setLoadedKey(key);
      })
      .catch(() => {
        if (cancelled) return;
        setError("Couldn't load recent activity.");
        setLoadedKey(key);
      });
    return () => {
      cancelled = true;
    };
  }, [canView, refreshKey]);

  return (
    <div className="flex flex-col gap-8 p-6">
      <header>
        <p className="text-xs font-semibold tracking-wide text-primary uppercase">FastFrame</p>
        <h2 className="mt-1 font-display text-3xl font-semibold tracking-tight">Overview</h2>
        <p className="mt-2 text-sm text-muted-foreground">Use the search bar in the sidebar to jump to a model.</p>
      </header>

      {canView ? (
        <section className="rounded-xl border border-border bg-card">
          <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
            <h3 className="font-display text-base font-semibold">Recent activity</h3>
            <Link to="/auditlog" className="text-sm font-medium text-primary hover:underline">
              View full history
            </Link>
          </div>
          {pending && rows === null && !error ? <p className="px-4 py-6 text-sm text-muted-foreground">Loading…</p> : null}
          {error ? <p className="px-4 py-6 text-sm text-muted-foreground">{error}</p> : null}
          {rows && rows.length === 0 ? (
            <p className="px-4 py-6 text-sm text-muted-foreground">Nothing has happened yet.</p>
          ) : null}
          {rows && rows.length ? (
            <ul>
              {rows.map((row) => {
                const action = String(row.action ?? "");
                const target = String(row.object_repr || row.model_name || "");
                return (
                  <li key={String(row.id)} className="flex gap-3 border-b border-border px-4 py-3 last:border-b-0">
                    <span
                      className={`mt-1.5 size-2 shrink-0 rounded-full ${
                        action === "delete" ? "bg-destructive" : action === "create" ? "bg-[#0F9F6E]" : "bg-primary"
                      }`}
                      aria-hidden="true"
                    />
                    <div className="min-w-0">
                      <p className="text-sm">
                        <span className="font-medium">{String(row.username || "System")}</span>{" "}
                        {ACTION_LABEL[action] ?? action}
                        {target ? <span className="text-muted-foreground"> {target}</span> : null}
                      </p>
                      <p className="text-xs text-muted-foreground">{relativeTime(String(row.created_at ?? ""))}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
