import { useEffect, useMemo, useState } from "react";
import { Admin, Resource, Title, useGetList } from "react-admin";
import { Link } from "react-router-dom";

import { API_URL, type ModelSchema, type SchemaResponse } from "./api";
import { dataProvider } from "./dataProvider";
import { FrameLayout } from "./layout";
import { buildResourceViews } from "./resources";
import { theme } from "./theme";
import { buildUserViews, isUserModel } from "./users";

function ResourceTile({ model }: { model: ModelSchema }) {
  const { total, isPending } = useGetList(model.resource, {
    pagination: { page: 1, perPage: 1 },
    sort: { field: "id", order: "ASC" },
  });
  const people = isUserModel(model);
  return (
    <Link to={`/${model.resource}`} className={people ? "tile tile-people" : "tile"}>
      <span className="tile-app">{model.appLabel}</span>
      <span className="tile-count">{isPending ? "—" : (total ?? 0)}</span>
      <span className="tile-label">{model.labelPlural}</span>
      <span className="tile-hint">Open the list</span>
    </Link>
  );
}

function makeDashboard(models: ModelSchema[]) {
  return function Dashboard() {
    return (
      <div className="home">
        <Title title="Overview" />
        <header className="home-head">
          <p className="eyebrow">FastFrame</p>
          <h1>Overview</h1>
        </header>
        <div className="home-grid">
          {models.map((model) => (
            <ResourceTile key={model.resource} model={model} />
          ))}
        </div>
      </div>
    );
  };
}

export default function App() {
  const [models, setModels] = useState<ModelSchema[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/schema`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Admin API returned HTTP ${response.status}. Is the FastFrame server running?`);
        }
        return (await response.json()) as SchemaResponse;
      })
      .then((body) => setModels(body.models))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        setError(
          `${message}. Start the API, then reload. The admin reads ${API_URL}/schema.`,
        );
      });
  }, []);

  const resources = useMemo(
    () =>
      (models ?? []).map((model) => ({
        model,
        views: isUserModel(model) ? buildUserViews(model, models ?? []) : buildResourceViews(model, models ?? []),
      })),
    [models],
  );

  const Dashboard = useMemo(() => (models ? makeDashboard(models) : undefined), [models]);

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
