export type CinemaSource = {
  title: string;
  url?: string;
  snippet?: string;
};

export type LearningChallenge = {
  prompt?: string;
  answer?: string;
  vocabulary?: string[];
};

export type CinemaResult = {
  success?: boolean;
  result?: string;
  intelligence?: string;
  summary?: string;
  sources?: CinemaSource[];
  learning_challenge?: LearningChallenge;
  personalisation?: string | {
    applied?: boolean;
    message?: string;
  };
  error?: string;
};

export type CinemaActionResponse = {
  success?: boolean;
  configured?: boolean;
  feedback?: string;
  error?: string;
  [key: string]: unknown;
};

const USER_ID = "hackathon-judge";

/**
 * API origin.
 *
 * Local development:
 *   http://localhost:8000
 *
 * Production/hackathon deployment:
 *   configure VITE_API_BASE_URL to the protected API origin.
 *
 * Keeping this configurable prevents the browser from depending
 * on a hard-coded production hostname.
 */
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000"
).replace(/\/$/, "");

async function request<T>(
  path: string,
  options: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    },
  );

  if (!response.ok) {
    let detail = "";

    try {
      const body = (await response.json()) as {
        detail?: string;
        error?: string;
      };

      detail = body.detail || body.error || "";
    } catch {
      // The API may return an empty/non-JSON error body.
    }

    throw new Error(
      detail
        ? `${path} returned HTTP ${response.status}: ${detail}`
        : `${path} returned HTTP ${response.status}.`,
    );
  }

  return (await response.json()) as T;
}

export async function runCinema(
  message: string,
): Promise<CinemaResult> {
  const cleanMessage = message.trim();

  if (!cleanMessage) {
    throw new Error(
      "Cinema question cannot be empty.",
    );
  }

  return request<CinemaResult>(
    "/api/cinema",
    {
      method: "POST",
      body: JSON.stringify({
        message: cleanMessage,
        userId: USER_ID,
        language: "French",
        learnerLevel: "B2",
      }),
    },
  );
}

export async function runCinemaAction(
  action: "save" | "challenge",
  payload: Record<string, unknown>,
): Promise<CinemaActionResponse> {
  return request<CinemaActionResponse>(
    "/api/cinema/action",
    {
      method: "POST",
      body: JSON.stringify({
        action,
        payload,
      }),
    },
  );
}

export function getSpotifySearchUrl(
  query: string,
): string {
  return `https://open.spotify.com/search/${encodeURIComponent(
    query.trim(),
  )}`;
}

export function getYouTubeSearchUrl(
  query: string,
): string {
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(
    query.trim(),
  )}`;
}