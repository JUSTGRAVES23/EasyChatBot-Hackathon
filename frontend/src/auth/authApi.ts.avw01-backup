export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  detail: string;
  expires_at: string;
}

export interface SessionResponse {
  authenticated: boolean;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface RegisterResponse {
  detail: string;
}

export interface VerifyEmailResponse {
  detail: string;
}

export class AuthenticationApiError extends Error {
  readonly status: number;

  constructor(
    message: string,
    status: number,
  ) {
    super(message);
    this.name = "AuthenticationApiError";
    this.status = status;
  }
}

async function parseApiError(
  response: Response,
  fallback: string,
): Promise<AuthenticationApiError> {
  let detail = fallback;

  try {
    const body: unknown = await response.json();

    if (
      body &&
      typeof body === "object" &&
      "detail" in body &&
      typeof body.detail === "string" &&
      body.detail.trim()
    ) {
      detail = body.detail;
    }
  } catch {
    // Preserve safe generic API error.
  }

  return new AuthenticationApiError(detail, response.status);
}

export async function getSession(): Promise<SessionResponse> {
  const response = await fetch("/auth/session", {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw await parseApiError(
      response,
      `Authentication session check failed (${response.status}).`,
    );
  }

  return response.json() as Promise<SessionResponse>;
}

export async function register(
  credentials: RegisterRequest,
): Promise<RegisterResponse> {
  const response = await fetch("/auth/register", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw await parseApiError(
      response,
      "Unable to create the account. Please try again later.",
    );
  }

  return response.json() as Promise<RegisterResponse>;
}

export async function verifyEmail(
  token: string,
): Promise<VerifyEmailResponse> {
  const response = await fetch(
    `/auth/verify-email?token=${encodeURIComponent(token)}`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw await parseApiError(
      response,
      "This verification link is invalid or has expired.",
    );
  }

  return response.json() as Promise<VerifyEmailResponse>;
}

export async function login(
  credentials: LoginRequest,
): Promise<LoginResponse> {
  const response = await fetch("/auth/login", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw await parseApiError(
      response,
      `Authentication failed (${response.status}).`,
    );
  }

  return response.json() as Promise<LoginResponse>;
}

export async function logout(): Promise<void> {
  const response = await fetch("/auth/logout", {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok && response.status !== 204) {
    throw new AuthenticationApiError(
      `Logout failed (${response.status}).`,
      response.status,
    );
  }
}