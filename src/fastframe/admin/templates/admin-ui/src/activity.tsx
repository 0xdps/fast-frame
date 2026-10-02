import { useGetList } from "react-admin";
import { Link } from "react-router-dom";

import type { ModelSchema } from "./api";

const ACTION_LABEL: Record<string, string> = {
  create: "created",
  update: "updated",
  delete: "deleted",
};

/** Dashboard preview only — the full table lives at `/auditlog`. */
const PREVIEW_SIZE = 5;

/**
 * The API serializes datetimes without a timezone suffix (naive, but
 * actually UTC — see `serialize_value`/`DateTimeField.auto_now_add`).
 * `Date` parses a bare "YYYY-MM-DDTHH:mm:ss" as *local* time, so treat it
 * as UTC explicitly unless it already carries a 'Z' or +/-offset.
 */
function parseApiDate(iso: string): number {
  const hasOffset = /(Z|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(hasOffset ? iso : `${iso}Z`).getTime();
}

function relativeTime(iso: string): string {
  const then = parseApiDate(iso);
  if (Number.isNaN(then)) return "";
  let diff = (then - Date.now()) / 1000; // seconds; negative = past
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

/**
 * Short "Recent activity" preview on the dashboard, sourced from
 * `AuditLog`. Each row is just who did what, and when — the full table
 * (filters, search, source, exact timestamps) is one link away at
 * `/auditlog`, which is intentionally not listed in the sidebar.
 * Renders nothing if the current user can't view audit entries, or if
 * `AuditLog` isn't registered at all.
 */
export function RecentActivity({ models }: { models: ModelSchema[] }) {
  const auditModel = models.find((model) => model.resource === "auditlog");
  const canView = auditModel?.permissions.view ?? false;

  const { data, isPending, error } = useGetList(
    "auditlog",
    { pagination: { page: 1, perPage: PREVIEW_SIZE }, sort: { field: "created_at", order: "DESC" }, filter: {} },
    { enabled: canView },
  );

  if (!canView) return null;

  return (
    <section className="activity-panel">
      <div className="activity-head">
        <h2>Recent activity</h2>
        <Link to="/auditlog" className="activity-all">
          View full history
        </Link>
      </div>
      {isPending ? <p className="activity-empty">Loading…</p> : null}
      {error ? <p className="activity-empty">Couldn't load recent activity.</p> : null}
      {!isPending && !error && (!data || data.length === 0) ? (
        <p className="activity-empty">Nothing has happened yet.</p>
      ) : null}
      {data && data.length ? (
        <ul className="activity-list">
          {data.map((row) => {
            const action = String(row.action ?? "");
            const target = String(row.object_repr || row.model_name || "");
            return (
              <li key={String(row.id)} className="activity-item">
                <span className={`activity-icon activity-icon-${action}`} aria-hidden="true" />
                <div className="activity-body">
                  <p>
                    <span className="activity-actor">{String(row.username || "System")}</span>{" "}
                    {ACTION_LABEL[action] ?? action}
                    {target ? <span className="activity-target"> {target}</span> : null}
                  </p>
                  <span className="activity-meta">{relativeTime(String(row.created_at ?? ""))}</span>
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
}
