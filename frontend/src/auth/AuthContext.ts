import { createContext } from "react";

import type { LoginRequest } from "./authApi";

export type AuthStatus =
  | "unknown"
  | "authenticated"
  | "unauthenticated";

export interface AuthContextValue {
  status: AuthStatus;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const AuthContext =
  createContext<AuthContextValue | null>(null);

if (import.meta.env.DEV) {
  const existing = (
    window as typeof window & {
      __easychatbot_auth_context__?: typeof AuthContext;
    }
  ).__easychatbot_auth_context__;

  if (existing && existing !== AuthContext) {
    console.error(
      "[EasyChatBot Auth] DUPLICATE AuthContext detected",
      {
        existing,
        current: AuthContext,
        same: existing === AuthContext,
      },
    );
  }

  (
    window as typeof window & {
      __easychatbot_auth_context__?: typeof AuthContext;
    }
  ).__easychatbot_auth_context__ = AuthContext;
}