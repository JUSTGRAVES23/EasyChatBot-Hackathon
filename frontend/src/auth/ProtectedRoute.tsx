import {
  Navigate,
  useLocation,
} from "react-router-dom";

import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "./useAuth";

export default function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  const {
    status,
    refresh,
  } = useAuth();

  const location = useLocation();

  const [checking, setChecking] = useState(
    status === "unknown",
  );

  useEffect(() => {
    if (status !== "unknown") {
      setChecking(false);
      return;
    }

    let active = true;

    void refresh()
      .catch(() => {
        if (active) {
          /*
           * Fail closed from the frontend navigation
           * perspective. Backend authorization remains
           * authoritative.
           */
        }
      })
      .finally(() => {
        if (active) {
          setChecking(false);
        }
      });

    return () => {
      active = false;
    };
  }, [refresh, status]);

  if (checking) {
    return (
      <main aria-label="Authentication check">
        Checking access…
      </main>
    );
  }

  if (status !== "authenticated") {
    const redirect = encodeURIComponent(
      `${location.pathname}${location.search}`,
    );

    return (
      <Navigate
        to={`/login?redirect=${redirect}`}
        replace
      />
    );
  }

  return <>{children}</>;
}