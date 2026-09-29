import { useEffect, useMemo, useState } from "react";
import { Admin, Resource } from "react-admin";

import { API_URL, type ModelSchema, type SchemaResponse } from "./api";
import { dataProvider } from "./dataProvider";
import { makeDashboard } from "./dashboard";
import { makeFrameLayout } from "./layout";
import { buildResourceViews } from "./resources";
import { darkTheme, theme } from "./theme";
import { buildUserViews, isUserModel } from "./users";

export default function App() {
  const [models, setModels] = useState<ModelSchema[] | null>(null);
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

  const resources = useMemo(
    () =>
      (models ?? []).map((model) => ({
        model,
        views: isUserModel(model) ? buildUserViews(model, models ?? []) : buildResourceViews(model, models ?? []),
      })),
    [models],
  );

  const Dashboard = useMemo(() => (models ? makeDashboard(models) : undefined), [models]);
  const FrameLayout = useMemo(() => (models ? makeFrameLayout(models) : undefined), [models]);

  if (error) {
    return (
      <div className="boot-message">
        <h1>FastFrame Admin</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!models || !Dashboard || !FrameLayout) {
    return <p className="boot-message">Loading FastFrame Admin…</p>;
  }

  return (
    <Admin
      dataProvider={dataProvider}
      dashboard={Dashboard}
      layout={FrameLayout}
      theme={theme}
      darkTheme={darkTheme}
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
