export type CinemaSource = {
  title: string;
  url?: string;
  snippet?: string;
};

export type CinemaResult = {
  success?: boolean;
  result?: string;
  intelligence?: string;
  summary?: string;
  sources?: CinemaSource[];
  learning_challenge?: {
    prompt?: string;
    answer?: string;
    vocabulary?: string[];
  };
  personalisation?: string | { applied?: boolean; message?: string };
  error?: string;
};

export type CinemaActionResult = {
  success?: boolean;
  configured?: boolean;
  result?: string;
  error?: string;
};

function asText(value: unknown): string | undefined {
  if (typeof value === "string") return value;
  if (value == null) return undefined;
  if (typeof value === "number" || typeof value === "boolean") return String(value);

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return undefined;
  }
}

function normalizeSource(value: unknown): CinemaSource | null {
  if (!value || typeof value !== "object") return null;

  const source = value as Record<string, unknown>;
  const title = asText(source.title) ?? "Untitled source";
  const url = asText(source.url);
  const snippet = asText(source.snippet);

  return {
    title,
    ...(url ? { url } : {}),
    ...(snippet ? { snippet } : {}),
  };
}

function normalizeCinemaResult(value: unknown): CinemaResult {
  if (!value || typeof value !== "object") {
    return {
      success: false,
      error: "Cinema service returned an invalid response.",
    };
  }

  const raw = value as Record<string, unknown>;

  const sources = Array.isArray(raw.sources)
    ? raw.sources
        .map(normalizeSource)
        .filter((source): source is CinemaSource => source !== null)
    : undefined;

  const challenge =
    raw.learning_challenge && typeof raw.learning_challenge === "object"
      ? (raw.learning_challenge as Record<string, unknown>)
      : undefined;

  const vocabulary = Array.isArray(challenge?.vocabulary)
    ? challenge.vocabulary
        .map(asText)
        .filter((item): item is string => Boolean(item))
    : undefined;

  let personalisation: CinemaResult["personalisation"];

  if (typeof raw.personalisation === "string") {
    personalisation = raw.personalisation;
  } else if (raw.personalisation && typeof raw.personalisation === "object") {
    const value = raw.personalisation as Record<string, unknown>;
    const message = asText(value.message);
    personalisation = {
      applied: Boolean(value.applied),
      ...(message ? { message } : {}),
    };
  }

  const resultText = asText(raw.result);
  const intelligenceText = asText(raw.intelligence);
  const summaryText = asText(raw.summary);
  const errorText = asText(raw.error);

  return {
    success: raw.success !== false,
    ...(resultText ? { result: resultText } : {}),
    ...(intelligenceText ? { intelligence: intelligenceText } : {}),
    ...(summaryText ? { summary: summaryText } : {}),
    ...(sources ? { sources } : {}),
    ...(challenge
      ? {
          learning_challenge: {
            ...(asText(challenge.prompt)
              ? { prompt: asText(challenge.prompt) }
              : {}),
            ...(asText(challenge.answer)
              ? { answer: asText(challenge.answer) }
              : {}),
            ...(vocabulary ? { vocabulary } : {}),
          },
        }
      : {}),
    ...(personalisation ? { personalisation } : {}),
    ...(errorText ? { error: errorText } : {}),
  };
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();

  if (!text.trim()) return {};

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return {
      success: false,
      error: "Cinema service returned an invalid JSON response.",
    };
  }
}

export async function runCinema(
  message: string,
  options: {
    userId?: string;
    language?: string;
    learnerLevel?: string;
  } = {},
): Promise<CinemaResult> {
  const response = await fetch("/api/cinema", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      user_id: options.userId ?? "hackathon-judge",
      language: options.language ?? "French",
      learner_level: options.learnerLevel ?? "B2",
    }),
  });

  const payload = await parseJson(response);

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object"
        ? asText((payload as Record<string, unknown>).detail)
        : undefined;

    throw new Error(
      detail || `Cinema service returned HTTP ${response.status}.`,
    );
  }

  return normalizeCinemaResult(payload);
}

export async function runCinemaAction(
  action: "save" | "challenge",
  payload: Record<string, unknown>,
): Promise<CinemaActionResult> {
  const response = await fetch("/api/cinema/action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });

  const data = await parseJson(response);

  if (!response.ok) {
    const detail =
      data && typeof data === "object"
        ? asText((data as Record<string, unknown>).detail)
        : undefined;

    throw new Error(
      detail || `Cinema action returned HTTP ${response.status}.`,
    );
  }

  if (!data || typeof data !== "object") {
    return {
      success: false,
      error: "Cinema action returned an invalid response.",
    };
  }

  const raw = data as Record<string, unknown>;
  const resultText = asText(raw.result);
  const errorText = asText(raw.error);

  return {
    success: raw.success !== false,
    ...(typeof raw.configured === "boolean"
      ? { configured: raw.configured }
      : {}),
    ...(resultText ? { result: resultText } : {}),
    ...(errorText ? { error: errorText } : {}),
  };
}
