export interface AuthUserDto {
  readonly id: string;
  readonly tenant_id: string;
  readonly email: string;
  readonly full_name: string;
  readonly business_name: string;
  readonly initials: string;
  readonly plan: string;
}

export interface RegisterInput {
  readonly email: string;
  readonly password: string;
  readonly fullName: string;
  readonly businessName: string;
}

export interface LoginInput {
  readonly email: string;
  readonly password: string;
}

export class AuthApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/auth${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new AuthApiError(problem?.detail ?? "Account service is unavailable.", response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const authApi = {
  me: () => request<AuthUserDto>("/me"),
  register: (input: RegisterInput) =>
    request<AuthUserDto>("/register", {
      method: "POST",
      body: JSON.stringify({
        email: input.email,
        password: input.password,
        full_name: input.fullName,
        business_name: input.businessName,
      }),
    }),
  login: (input: LoginInput) =>
    request<AuthUserDto>("/login", { method: "POST", body: JSON.stringify(input) }),
  logout: () => request<void>("/logout", { method: "POST" }),
};
