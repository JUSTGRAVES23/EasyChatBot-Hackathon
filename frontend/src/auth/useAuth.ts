import { useContext } from "react";

import {
  AuthContext,
  type AuthContextValue,
} from "./AuthContext";

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    const diagnosticWindow =
      window as typeof window & {
        __easychatbot_auth_context__?: typeof AuthContext;
      };

    console.error(
      "[EasyChatBot Auth] useAuth context lookup FAILED",
      {
        context,
        currentContext: AuthContext,
        registeredContext:
          diagnosticWindow.__easychatbot_auth_context__,
        sameContext:
          diagnosticWindow.__easychatbot_auth_context__ ===
          AuthContext,
        currentUrl: window.location.href,
      },
    );

    throw new Error(
      "useAuth must be used within an AuthProvider.",
    );
  }

  console.log(
    "[EasyChatBot Auth] useAuth context lookup succeeded",
    {
      status: context.status,
    },
  );

  return context;
}