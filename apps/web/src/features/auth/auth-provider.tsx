import { type ReactNode, useEffect, useMemo, useState } from "react";

import { authApi, AuthApiError, type AuthUserDto, type LoginInput, type RegisterInput } from "./auth-api";
import { AuthContext, type AuthState, type AuthenticatedUser } from "./auth-context";

function toUser(dto: AuthUserDto): AuthenticatedUser {
  return { id: dto.id, tenantId: dto.tenant_id, email: dto.email, name: dto.full_name, businessName: dto.business_name, initials: dto.initials, plan: dto.plan };
}

export function AuthProvider({ children, initialUser }: { readonly children: ReactNode; readonly initialUser?: AuthenticatedUser }) {
  const [status, setStatus] = useState<AuthState["status"]>(initialUser ? "authenticated" : "loading");
  const [user, setUser] = useState<AuthenticatedUser | null>(initialUser ?? null);

  useEffect(() => {
    if (initialUser) return;
    let active = true;
    void authApi.me().then((dto) => { if (active) { setUser(toUser(dto)); setStatus("authenticated"); } }).catch((error: unknown) => {
      if (!active) return;
      if (error instanceof AuthApiError && (error.status === 401 || error.status === 503)) setStatus("anonymous");
      else setStatus("anonymous");
    });
    return () => { active = false; };
  }, [initialUser]);

  const value = useMemo<AuthState>(() => {
    const authenticate = async (operation: Promise<AuthUserDto>) => { const dto = await operation; setUser(toUser(dto)); setStatus("authenticated"); };
    const actions = {
      register: (input: RegisterInput) => authenticate(authApi.register(input)),
      login: (input: LoginInput) => authenticate(authApi.login(input)),
      logout: async () => { await authApi.logout(); setUser(null); setStatus("anonymous"); },
    };
    if (status === "authenticated" && user) return { status, user, ...actions };
    return { status: status === "loading" ? "loading" : "anonymous", user: null, ...actions };
  }, [status, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
