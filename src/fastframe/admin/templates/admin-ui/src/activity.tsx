import { useGetList } from "react-admin";
import { Link } from "react-router-dom";

import type { ModelSchema } from "./api";

const ACTION_LABEL: Record<string, string> = {
  create: "created",
  update: "updated",
  delete: "deleted",
};

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
 * "Recent activity" dashboard panel, sourced from `AuditLog` — the same
 * model that already records every admin/API create/update/delete (see
 * `fastframe.admin.audit`). Renders nothing if the current user can't view
 * audit entries, or if `AuditLog` isn't registered at all.
 */
export function RecentActivity({ models }: { models: ModelSchema[] }) {
  const auditModel = models.find((model) => model.resource === "auditlog");
  const canView = auditModel?.permissions.view ?? false;

  const { data, isPending, error } = useGetList(
    "auditlog",
    { pagination: { page: 1, perPage: 8 }, sort: { field: "created_at", order: "DESC" }, filter: {} },
    { enabled: canView },
  );

  if (!canView) return null;

  return (
    <section className="activity-panel">
      <h2>Recent activity</h2>
      {isPending ? <p className="activity-empty">Loading…</p> : null}
      {error ? <p className="activity-empty">Couldn't load recent activity.</p> : null}
      {!isPending && !error && (!data || data.length === 0) ? (
        <p className="activity-empty">Nothing has happened yet.</p>
      ) : null}
      {data && data.length ? (
        <ul className="activity-list">
          {data.map((row) => {
            const modelName = String(row.model_name ?? "").toLowerCase();
            const resource = models.find((model) => model.resource === modelName);
            const target = resource && row.object_id ? `/${resource.resource}/${row.object_id}` : undefined;
            const action = String(row.action ?? "");
            const body = (
              <>
                <span className="activity-actor">{String(row.username || "System")}</span>{" "}
                {ACTION_LABEL[action] ?? action}{" "}
                <span className="activity-target">{String(row.object_repr || row.model_name || "")}</span>
              </>
            );
            return (
              <li key={String(row.id)} className="activity-item">
                <span className={`activity-icon activity-icon-${action}`} aria-hidden="true" />
                <div className="activity-body">
                  <p>{target ? <Link to={target}>{body}</Link> : body}</p>
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
