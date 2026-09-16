import {
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getSession,
  login as loginRequest,
  logout as logoutRequest,
  type LoginRequest,
} from "./authApi";

import { AuthContext } from "./AuthContext";

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [status, setStatus] =
    useState<
      "unknown" |
      "authenticated" |
      "unauthenticated"
    >("unknown");

  const refresh = useCallback(async () => {
    try {
      const session = await getSession();

      if (session.authenticated) {
        setStatus("authenticated");
      } else {
        setStatus("unauthenticated");
      }
    } catch (error) {
      /*
       * A 401 is an expected unauthenticated state.
       *
       * Unexpected API/network failures are fail-closed for
       * frontend navigation. The backend remains the authoritative
       * security boundary.
       */
      setStatus("unauthenticated");

      throw error;
    }
  }, []);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      await loginRequest(credentials);

      /*
       * The backend has now established its existing
       * HttpOnly easychatbot_session cookie.
       *
       * No credential/session value is stored in browser
       * application storage.
       */
      setStatus("authenticated");
    },
    [],
  );

  const logout = useCallback(async () => {
    await logoutRequest();

    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({
      status,
      login,
      logout,
      refresh,
    }),
    [
      status,
      login,
      logout,
      refresh,
    ],
  );

  /*
   * TEMPORARY DEVELOPMENT DIAGNOSTIC
   *
   * This allows us to determine whether Vite is loading
   * multiple AuthContext module instances.
   *
   * This must be removed after the root cause is confirmed.
   */
  if (import.meta.env.DEV) {
    const diagnosticWindow =
      window as typeof window & {
        __easychatbot_auth_context__?: typeof AuthContext;
      };

    console.log(
      "[EasyChatBot Auth] AuthProvider rendering",
      {
        status,
        context:
          diagnosticWindow.__easychatbot_auth_context__,
        sameContext:
          diagnosticWindow.__easychatbot_auth_context__ ===
          AuthContext,
      },
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}