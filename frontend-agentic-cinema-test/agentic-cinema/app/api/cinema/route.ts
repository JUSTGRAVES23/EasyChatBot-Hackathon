import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type CinemaRequest = {
  message: string;
  userId?: string;
  language?: string;
  learnerLevel?: string;
};

function timeoutMs() {
  const parsed = Number(process.env.CINEMA_BACKEND_TIMEOUT_MS ?? "60000");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 60000;
}

export async function POST(request: NextRequest) {
  const backendUrl = process.env.CINEMA_BACKEND_URL?.trim();

  if (!backendUrl) {
    return NextResponse.json(
      {
        success: false,
        error: "CINEMA_BACKEND_URL is not configured. Connect this UI to the existing cinema/application backend."
      },
      { status: 503 }
    );
  }

  let payload: CinemaRequest;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ success: false, error: "Invalid JSON request." }, { status: 400 });
  }

  if (!payload.message?.trim()) {
    return NextResponse.json({ success: false, error: "message is required." }, { status: 400 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs());

  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json"
    };

    const token = process.env.CINEMA_BACKEND_TOKEN?.trim();
    if (token) headers.Authorization = `Bearer ${token}`;

    // The backend adapter intentionally accepts a small business-level contract.
    // It can point at the existing application API or a server-side Agent Runtime adapter.
    const response = await fetch(backendUrl, {
      method: "POST",
      headers,
      body: JSON.stringify({
        message: payload.message.trim(),
        user_id: payload.userId ?? "hackathon-judge",
        language: payload.language ?? "French",
        learner_level: payload.learnerLevel ?? "B2"
      }),
      signal: controller.signal,
      cache: "no-store"
    });

    const text = await response.text();
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      data = { success: response.ok, result: text };
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    const message =
      error instanceof Error && error.name === "AbortError"
        ? "Cinema backend request timed out."
        : error instanceof Error
          ? error.message
          : "Cinema backend request failed.";

    return NextResponse.json({ success: false, error: message }, { status: 502 });
  } finally {
    clearTimeout(timer);
  }
}
