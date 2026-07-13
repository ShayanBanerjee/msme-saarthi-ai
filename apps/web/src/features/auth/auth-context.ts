import { createContext, useContext } from "react";

import type { LoginInput, RegisterInput } from "./auth-api";

export interface AuthenticatedUser {
  readonly id: string;
  readonly tenantId: string;
  readonly email: string;
  readonly name: string;
  readonly businessName: string;
  readonly initials: string;
  readonly plan: string;
}

interface AuthActions {
  readonly register: (input: RegisterInput) => Promise<void>;
  readonly login: (input: LoginInput) => Promise<void>;
  readonly logout: () => Promise<void>;
}

export type AuthState =
  | ({ readonly status: "loading"; readonly user: null } & AuthActions)
  | ({ readonly status: "anonymous"; readonly user: null } & AuthActions)
  | ({ readonly status: "authenticated"; readonly user: AuthenticatedUser } & AuthActions);

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
