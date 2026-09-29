import { useEffect, useState } from "react";

import { API_URL } from "./api";

export interface CurrentUser {
  id: string | number | null;
  username: string | null;
  email: string | null;
  isSuperuser: boolean;
  canAccessAdmin: boolean;
}

/**
 * Fetches the currently authenticated admin user from `/me`.
 *
 * There's no `authProvider` wired up for the admin UI (the session cookie
 * is set by the server-rendered login page, outside the SPA — see
 * `views.py`), so this is a plain fetch rather than react-admin's
 * `useAuthenticated`/`usePermissions`. `null` means "not loaded yet or not
 * authenticated"; a page that's actually rendering already implies a valid
 * session (the server would have served the login page otherwise), so this
 * is only ever transiently null while the request is in flight.
 */
export function useCurrentUser(): CurrentUser | null {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/me`, { headers: { Accept: "application/json" } })
      .then(async (response) => {
        if (!response.ok) return null;
        const body = (await response.json()) as { data?: CurrentUser };
        return body.data ?? null;
      })
      .then((data) => {
        if (!cancelled) setUser(data);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return user;
}
