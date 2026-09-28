import { useEffect, useMemo, useState } from "react";
import { Admin, Resource, Title } from "react-admin";
import { Link } from "react-router-dom";

import { API_URL, type ModelSchema, type SchemaResponse } from "./api";
import { dataProvider } from "./dataProvider";
import { FrameLayout } from "./layout";
import { buildResourceViews } from "./resources";
import { theme } from "./theme";
import { buildUserViews, isUserModel } from "./users";

function modelCount(model: ModelSchema, counts: Record<string, number>): number {
  return counts[model.resource] ?? 0;
}

function ResourceTile({ model, count }: { model: ModelSchema; count: number }) {
  const people = isUserModel(model);
  return (
    <Link to={`/${model.resource}`} className={people ? "tile tile-people" : "tile"}>
      <span className="tile-app">{model.appLabel}</span>
      <span className="tile-count">{count}</span>
      <span className="tile-label">{model.labelPlural}</span>
      <span className="tile-hint">Open the list</span>
    </Link>
  );
}

function makeDashboard(models: ModelSchema[], counts: Record<string, number>) {
  // Preserve schema order, but group per app for display.
  const grouped = new Map<string, ModelSchema[]>();
  for (const model of models) {
    const label = model.appLabel || "app";
    const bucket = grouped.get(label) ?? [];
    bucket.push(model);
    grouped.set(label, bucket);
  }

  return function Dashboard() {
    return (
      <div className="home">
        <Title title="Overview" />
        <header className="home-head">
          <p className="eyebrow">FastFrame</p>
          <h1>Overview</h1>
        </header>
        {[...grouped.entries()].map(([appLabel, appModels]) => (
          <section key={appLabel} className="home-app">
            <h2 className="home-app-label">{appLabel}</h2>
            <div className="home-grid">
              {appModels.map((model) => (
                <ResourceTile
                  key={model.resource}
                  model={model}
                  count={modelCount(model, counts)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    );
  };
}

export default function App() {
  const [models, setModels] = useState<ModelSchema[] | null>(null);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/schema`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Admin API returned HTTP ${response.status}. Is the FastFrame server running?`);
        }
        return (await response.json()) as SchemaResponse;
      })
      .then((body) => {
        if (!cancelled) setModels(body.models);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : String(err);
        setError(
          `${message}. Start the API, then reload. The admin reads ${API_URL}/schema.`,
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Row counts live on a separate endpoint so /schema stays static and the
  // dashboard doesn't fire one list request per model.
  useEffect(() => {
    fetch(`${API_URL}/counts`)
      .then(async (response) => {
        if (!response.ok) return {};
        const body = (await response.json()) as { counts?: Record<string, number> };
        return body.counts ?? {};
      })
      .then((c) => setCounts(c))
      .catch(() => setCounts({}));
  }, []);

  const resources = useMemo(
    () =>
      (models ?? []).map((model) => ({
        model,
        views: isUserModel(model) ? buildUserViews(model, models ?? []) : buildResourceViews(model, models ?? []),
      })),
    [models],
  );

  const Dashboard = useMemo(
    () => (models ? makeDashboard(models, counts) : undefined),
    [models, counts],
  );

  if (error) {
    return (
      <div className="boot-message">
        <h1>FastFrame Admin</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!models || !Dashboard) {
    return <p className="boot-message">Loading FastFrame Admin…</p>;
  }

  return (
    <Admin
      dataProvider={dataProvider}
      dashboard={Dashboard}
      layout={FrameLayout}
      theme={theme}
      title="FastFrame Admin"
    >
      {resources.map(({ model, views }) => (
        <Resource
          key={model.resource}
          name={model.resource}
          options={{ label: model.labelPlural }}
          list={views.list}
          edit={views.edit}
          create={views.create}
          recordRepresentation={views.recordRepresentation}
        />
      ))}
    </Admin>
  );
}
