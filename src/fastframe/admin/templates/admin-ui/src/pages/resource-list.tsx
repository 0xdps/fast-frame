import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { ModelSchema } from "../api";
import { useAdmin } from "../admin-state";
import { Button } from "../components/ui/button";
import { ConfirmDialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { deleteRecords, listRecords } from "../lib/client";
import { cn } from "../lib/cn";
import {
  fieldForColumn,
  formatCell,
  listColumns,
  recordId,
  relatedObjects,
  resourceForReference,
  sortFromOrdering,
} from "../lib/format";

function RecordCell({
  row,
  column,
  model,
  models,
}: {
  row: Record<string, unknown>;
  column: string;
  model: ModelSchema;
  models: ModelSchema[];
}) {
  const field = fieldForColumn(model, column);
  if (!field?.reference) return formatCell(row, column, model);
  const related = relatedObjects(row, field);
  if (!related.length) return "—";
  const resource = resourceForReference(models, field.reference, model);
  return (
    <span className="inline-flex max-w-full flex-wrap gap-x-2">
      {related.map((item) =>
        resource ? (
          <Link
            key={item.id}
            to={`/${resource}/${item.id}`}
            className="truncate font-medium text-primary hover:underline"
            onClick={(event) => event.stopPropagation()}
          >
            {item.label}
          </Link>
        ) : (
          <span key={item.id} className="truncate">
            {item.label}
          </span>
        ),
      )}
    </span>
  );
}

export function ResourceList() {
  const { resource = "" } = useParams();
  const { models, refreshKey, refresh } = useAdmin();
  const model = models.find((item) => item.resource === resource);
  const navigate = useNavigate();
  const columns = useMemo(() => (model ? listColumns(model) : []), [model]);
  const initialSort = model ? sortFromOrdering(model.ordering) : { field: "id", order: "ASC" as const };
  const perPage = model?.listPerPage || 25;

  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState(initialSort.field);
  const [sortOrder, setSortOrder] = useState<"ASC" | "DESC">(initialSort.order);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [scope, setScope] = useState(resource);
  const [pagedQuery, setPagedQuery] = useState(debouncedQuery);
  const [loadedKey, setLoadedKey] = useState("");

  if (scope !== resource) {
    setScope(resource);
    setPage(1);
    setSortField(initialSort.field);
    setSortOrder(initialSort.order);
    setQuery("");
    setDebouncedQuery("");
    setPagedQuery("");
    setSelected([]);
    setRows([]);
    setTotal(0);
    setError(null);
    setLoadedKey("");
  } else if (pagedQuery !== debouncedQuery) {
    setPagedQuery(debouncedQuery);
    setPage(1);
  }

  const fetchKey = `${resource}|${page}|${perPage}|${sortField}|${sortOrder}|${debouncedQuery}|${refreshKey}`;
  const pending = Boolean(model) && loadedKey !== fetchKey;

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (!model || scope !== resource) return;
    let cancelled = false;
    const key = fetchKey;
    listRecords(model.resource, {
      page,
      perPage,
      sortField,
      sortOrder,
      q: debouncedQuery || undefined,
    })
      .then((result) => {
        if (cancelled) return;
        setRows(result.data);
        setTotal(result.total);
        setSelected([]);
        setError(null);
        setLoadedKey(key);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Could not load records.");
        setLoadedKey(key);
      });
    return () => {
      cancelled = true;
    };
  }, [model, scope, resource, page, perPage, sortField, sortOrder, debouncedQuery, refreshKey, fetchKey]);

  if (!model) {
    return <p className="p-6 text-sm text-muted-foreground">This model is not in the admin.</p>;
  }

  const ids = rows.map((row) => recordId(row, model)).filter(Boolean);
  const allSelected = ids.length > 0 && ids.every((id) => selected.includes(id));
  const from = total === 0 ? 0 : (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);
  const canOpen = model.permissions.edit || model.permissions.view;

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder((order) => (order === "ASC" ? "DESC" : "ASC"));
    } else {
      setSortField(field);
      setSortOrder("ASC");
    }
    setPage(1);
  };

  const removeSelected = async () => {
    setDeleting(true);
    try {
      await deleteRecords(model.resource, selected);
      setConfirming(false);
      setSelected([]);
      refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not delete the selected records.");
      setConfirming(false);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-2xl font-semibold tracking-tight">{model.labelPlural}</h2>
        {model.permissions.create ? (
          <Button asChild>
            <Link to={`/${model.resource}/create`}>Add {model.label}</Link>
          </Button>
        ) : null}
      </div>

      {model.searchFields.length ? (
        <Input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Search ${model.labelPlural.toLowerCase()}`}
          aria-label={`Search ${model.labelPlural}`}
          className="max-w-sm"
        />
      ) : null}

      {error ? (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        {model.permissions.delete && selected.length ? (
          <div className="flex items-center justify-between gap-3 border-b border-border bg-accent px-4 py-2">
            <span className="text-sm">{selected.length} selected</span>
            <Button type="button" size="sm" variant="destructive" onClick={() => setConfirming(true)}>
              Delete
            </Button>
          </div>
        ) : null}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border text-xs tracking-wide text-muted-foreground uppercase">
              <tr>
                {model.permissions.delete ? (
                  <th className="w-10 px-3 py-3">
                    <input
                      type="checkbox"
                      aria-label="Select all on this page"
                      checked={allSelected}
                      onChange={(event) => setSelected(event.target.checked ? ids : [])}
                    />
                  </th>
                ) : null}
                {columns.map((column) => (
                  <th key={column.name} className="px-3 py-3 font-medium">
                    {column.sortable ? (
                      <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort(column.name)}>
                        {column.label}
                        {sortField === column.name ? <span>{sortOrder === "ASC" ? "↑" : "↓"}</span> : null}
                      </button>
                    ) : (
                      column.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pending && rows.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-muted-foreground" colSpan={columns.length + 1}>
                    Loading…
                  </td>
                </tr>
              ) : null}
              {!pending && rows.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-muted-foreground" colSpan={columns.length + 1}>
                    No records.
                  </td>
                </tr>
              ) : null}
              {rows.map((row) => {
                const id = recordId(row, model);
                return (
                  <tr
                    key={id || JSON.stringify(row)}
                    className={cn("border-b border-border last:border-b-0", canOpen && "cursor-pointer hover:bg-accent/70")}
                    onClick={() => {
                      if (canOpen && id) navigate(`/${model.resource}/${id}`);
                    }}
                  >
                    {model.permissions.delete ? (
                      <td className="px-3 py-3" onClick={(event) => event.stopPropagation()}>
                        <input
                          type="checkbox"
                          aria-label={`Select ${id}`}
                          checked={selected.includes(id)}
                          onChange={(event) =>
                            setSelected((current) =>
                              event.target.checked ? [...current, id] : current.filter((item) => item !== id),
                            )
                          }
                        />
                      </td>
                    ) : null}
                    {columns.map((column) => (
                      <td key={column.name} className="truncate px-3 py-3">
                        <RecordCell row={row} column={column.name} model={model} models={models} />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3 text-sm text-muted-foreground">
          <span>
            {from}–{to} of {total}
          </span>
          <div className="flex gap-2">
            <Button type="button" variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={page * perPage >= total}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={confirming}
        title={`Delete ${selected.length} ${selected.length === 1 ? model.label : model.labelPlural}?`}
        description="This cannot be undone."
        confirmLabel="Delete"
        pending={deleting}
        onOpenChange={setConfirming}
        onConfirm={() => void removeSelected()}
      />
    </div>
  );
}
