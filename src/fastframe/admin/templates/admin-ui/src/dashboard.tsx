import { Title } from "react-admin";

import type { ModelSchema } from "./api";
import { RecentActivity } from "./activity";

/**
 * Kept mostly empty on purpose — model browsing lives in the sidebar now
 * (searchable, grouped by app). The dashboard itself just orients the user
 * with a greeting and what's happened recently.
 */
export function makeDashboard(models: ModelSchema[]) {
  return function Dashboard() {
    return (
      <div className="home">
        <Title title="Overview" />
        <header className="home-head">
          <p className="eyebrow">FastFrame</p>
          <h1>Overview</h1>
          <p className="home-hint">Use the search bar in the sidebar to jump to a model.</p>
        </header>
        <RecentActivity models={models} />
      </div>
    );
  };
}
