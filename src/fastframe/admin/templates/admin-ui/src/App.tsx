import { useEffect, useState } from "react";
import { HashRouter, Route, Routes } from "react-router-dom";

import { AdminProvider } from "./admin-context";
import { API_URL, type ModelSchema, type SchemaResponse } from "./api";
import { Overview } from "./pages/overview";
import { ResourceForm } from "./pages/resource-form";
import { ResourceList } from "./pages/resource-list";
import { Shell } from "./shell";

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
        setError(`${message}. Start the API, then reload. The admin reads ${API_URL}/schema.`);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div className="boot-message">
        <h1>FastFrame Admin</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!models) {
    return <p className="boot-message">Loading FastFrame Admin…</p>;
  }

  return (
    <AdminProvider models={models}>
      <HashRouter>
        <Routes>
          <Route element={<Shell />}>
            <Route index element={<Overview />} />
            <Route path=":resource/create" element={<ResourceForm mode="create" />} />
            <Route path=":resource/:id" element={<ResourceForm mode="edit" />} />
            <Route path=":resource" element={<ResourceList />} />
          </Route>
        </Routes>
      </HashRouter>
    </AdminProvider>
  );
}
