import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import type { ModelSchema } from "../api";
import { useAdmin } from "../admin-state";
import { ColumnMenu } from "../components/column-menu";
import { FilterDrawer, filterLabel } from "../components/filter-drawer";
import { PageFrame } from "../components/page-frame";
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
} from "../lib/format";
import { PAGE_SIZE_OPTIONS, filterFields, readListQuery, writeListQuery, type ListQuery } from "../list-query";

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
            className="truncate font-medium text-link hover:underline"
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
  const location = useLocation();
  const query = useMemo(
    () => (model ? readListQuery(location.search, model) : null),
    [location.search, model],
  );
  const columns = useMemo(() => (model ? listColumns(model) : []), [model]);
  const visibleColumns = useMemo(
    () => columns.filter((column) => query?.columns.includes(column.name)),
    [columns, query],
  );
  const filters = useMemo(() => (model ? filterFields(model) : []), [model]);

  const [searchText, setSearchText] = useState(query?.q ?? "");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [loadedKey, setLoadedKey] = useState("");

  const replaceQuery = (next: ListQuery) => {
    if (!model) return;
    navigate({ pathname: location.pathname, search: writeListQuery(next, model) }, { replace: true });
  };

  useEffect(() => {
    setSearchText(query?.q ?? "");
    setFiltersOpen(false);
    setSelected([]);
  }, [resource, query?.q]);

  useEffect(() => {
    if (!model || !query) return;
    if (searchText === query.q) return;
    const timer = window.setTimeout(() => {
      replaceQuery({ ...query, q: searchText.trim(), page: 1 });
    }, 300);
    return () => window.clearTimeout(timer);
    // replaceQuery closes over the latest query; the timer only needs the text.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchText]);

  const fetchKey = query
    ? `${resource}|${query.page}|${query.perPage}|${query.sortField}|${query.sortOrder}|${query.q}|${JSON.stringify(query.filters)}|${refreshKey}`
    : "";
  const pending = Boolean(model) && loadedKey !== fetchKey;

  useEffect(() => {
    if (!model || !query) return;
    let cancelled = false;
    const key = fetchKey;
    listRecords(model.resource, {
      page: query.page,
      perPage: query.perPage,
      sortField: query.sortField,
      sortOrder: query.sortOrder,
      q: query.q || undefined,
      filters: query.filters,
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
  }, [model, query, resource, refreshKey, fetchKey]);

  if (!model || !query) {
    return (
      <PageFrame title="Not found">
        <p className="px-4 py-6 text-label text-muted-foreground lg:px-7">This model is not in the admin.</p>
      </PageFrame>
    );
  }

  const ids = rows.map((row) => recordId(row, model)).filter(Boolean);
  const allSelected = ids.length > 0 && ids.every((id) => selected.includes(id));
  const from = total === 0 ? 0 : (query.page - 1) * query.perPage + 1;
  const to = Math.min(query.page * query.perPage, total);
  const canOpen = model.permissions.edit || model.permissions.view;
  const activeFilters = filters.filter((field) => query.filters[field.name]);
  const filtered = Boolean(query.q) || activeFilters.length > 0;

  const toggleSort = (field: string) => {
    const order = query.sortField === field && query.sortOrder === "ASC" ? "DESC" : "ASC";
    replaceQuery({ ...query, sortField: field, sortOrder: order, page: 1 });
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
    <PageFrame
      title={model.labelPlural}
      meta={<span className="tabular-nums">{total.toLocaleString()}</span>}
      actions={
        model.permissions.create ? (
          <Button asChild size="sm">
            <Link to={`/${model.resource}/create`}>New {model.label}</Link>
          </Button>
        ) : null
      }
    >
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center gap-2 px-4 py-3 compact:py-2 lg:px-7">
          {model.searchFields.length ? (
            <Input
              type="search"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder={`Search ${model.labelPlural.toLowerCase()}`}
              aria-label={`Search ${model.labelPlural}`}
              className="h-8.5 w-full sm:w-72 compact:h-8"
            />
          ) : null}
          {filters.length ? (
            <Button type="button" variant="outline" size="sm" onClick={() => setFiltersOpen(true)}>
              Filters
              {activeFilters.length ? (
                <span className="rounded-full bg-primary px-1.5 text-caption text-primary-foreground">{activeFilters.length}</span>
              ) : null}
            </Button>
          ) : null}
          <span className="flex-1" />
          <ColumnMenu
            columns={columns}
            visible={query.columns}
            onChange={(next) => replaceQuery({ ...query, columns: next })}
          />
        </div>

        {activeFilters.length ? (
          <div className="flex flex-wrap items-center gap-1.5 px-4 pb-3 lg:px-7">
            {activeFilters.map((field) => (
              <button
                key={field.name}
                type="button"
                className="inline-flex h-7 items-center gap-1.5 rounded-full border border-line-strong bg-card px-2.5 text-note hover:bg-subtle"
                onClick={() => {
                  const next = { ...query.filters };
                  delete next[field.name];
                  replaceQuery({ ...query, filters: next, page: 1 });
                }}
              >
                <span className="text-muted-foreground">{field.label}</span>
                <span>{filterLabel(field, query.filters[field.name] ?? "")}</span>
                <span aria-hidden="true" className="text-muted-foreground">×</span>
                <span className="sr-only">Remove {field.label} filter</span>
              </button>
            ))}
            <button
              type="button"
              className="px-1.5 text-note text-muted-foreground hover:text-foreground"
              onClick={() => replaceQuery({ ...query, filters: {}, page: 1 })}
            >
              Clear
            </button>
          </div>
        ) : null}

        {error ? (
          <p className="mx-4 mb-2 rounded-box border border-destructive/30 bg-destructive/10 px-3 py-2 text-label text-destructive lg:mx-7">
            {error}
          </p>
        ) : null}

        <div className="flex min-h-0 flex-1 flex-col">
          {model.permissions.delete && selected.length ? (
            <div className="flex items-center justify-between gap-3 border-y border-line bg-selected px-4 py-2 lg:px-7">
              <span className="text-label">{selected.length} selected</span>
              <Button type="button" size="sm" variant="destructive" onClick={() => setConfirming(true)}>
                Delete
              </Button>
            </div>
          ) : null}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-label">
              <thead className="border-b border-line text-note text-muted-foreground">
                <tr style={{ height: "var(--list-head)" }}>
                  {model.permissions.delete ? (
                    <th className="w-10 px-3">
                      <input
                        type="checkbox"
                        aria-label="Select all on this page"
                        checked={allSelected}
                        onChange={(event) => setSelected(event.target.checked ? ids : [])}
                      />
                    </th>
                  ) : null}
                  {visibleColumns.map((column) => (
                    <th key={column.name} className="px-3 font-medium" style={{ paddingBlock: "var(--list-cell)" }}>
                      {column.sortable ? (
                        <button type="button" className="inline-flex items-center gap-1" onClick={() => toggleSort(column.name)}>
                          {column.label}
                          {query.sortField === column.name ? <span>{query.sortOrder === "ASC" ? "↑" : "↓"}</span> : null}
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
                    <td className="px-4 py-8 text-muted-foreground lg:px-7" colSpan={visibleColumns.length + 1}>
                      Loading…
                    </td>
                  </tr>
                ) : null}
                {!pending && rows.length === 0 ? (
                  <tr>
                    <td colSpan={visibleColumns.length + 1}>
                      <div className="mx-4 my-6 rounded-box border border-border bg-subtle px-5 py-8 text-center lg:mx-7">
                        <p className="font-medium">{filtered ? "No records match." : "No records yet."}</p>
                        <p className="mt-1 text-note text-muted-foreground">
                          {filtered
                            ? "Clear the search or filters to see every record."
                            : model.permissions.create
                              ? `Add the first ${model.label.toLowerCase()}.`
                              : "Nothing has been added."}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : null}
                {rows.map((row) => {
                  const id = recordId(row, model);
                  return (
                    <tr
                      key={id || JSON.stringify(row)}
                      className={cn(
                        "border-b border-line last:border-b-0 hover:bg-subtle",
                        selected.includes(id) && "bg-selected",
                        canOpen && "cursor-pointer",
                      )}
                      style={{ height: "var(--list-row)" }}
                      onClick={() => {
                        if (canOpen && id) navigate(`/${model.resource}/${id}`);
                      }}
                    >
                      {model.permissions.delete ? (
                        <td className="px-3" onClick={(event) => event.stopPropagation()}>
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
                      {visibleColumns.map((column) => (
                        <td key={column.name} className="px-3" style={{ paddingBlock: "var(--list-cell)" }}>
                          <span className="block max-w-[28rem] truncate">
                            <RecordCell row={row} column={column.name} model={model} models={models} />
                          </span>
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-3 text-label text-muted-foreground lg:px-7">
            <span className="tabular-nums">
              {from}–{to} of {total.toLocaleString()}
            </span>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1.5 text-note">
                Rows
                <select
                  aria-label="Rows per page"
                  value={query.perPage}
                  onChange={(event) => replaceQuery({ ...query, perPage: Number(event.target.value), page: 1 })}
                  className="h-8 rounded-field border border-line-strong bg-card px-2 text-label text-foreground"
                >
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
              <Button type="button" variant="outline" size="sm" disabled={query.page <= 1} onClick={() => replaceQuery({ ...query, page: query.page - 1 })}>
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={query.page * query.perPage >= total}
                onClick={() => replaceQuery({ ...query, page: query.page + 1 })}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>

      <FilterDrawer
        open={filtersOpen}
        model={model}
        fields={filters}
        filters={query.filters}
        onClose={() => setFiltersOpen(false)}
        onApply={(next) => {
          setFiltersOpen(false);
          replaceQuery({ ...query, filters: next, page: 1 });
        }}
      />
      <ConfirmDialog
        open={confirming}
        title={`Delete ${selected.length} ${selected.length === 1 ? model.label : model.labelPlural}?`}
        description="This cannot be undone."
        confirmLabel="Delete"
        pending={deleting}
        onOpenChange={setConfirming}
        onConfirm={() => void removeSelected()}
      />
    </PageFrame>
  );
}
