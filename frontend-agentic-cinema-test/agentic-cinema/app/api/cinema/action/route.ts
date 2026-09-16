import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type ActionPayload = {
  action: "save" | "challenge";
  payload: Record<string, unknown>;
};

export async function POST(request: NextRequest) {
  let body: ActionPayload;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ success: false, error: "Invalid JSON request." }, { status: 400 });
  }

  const endpoint =
    body.action === "save"
      ? process.env.CINEMA_SAVE_URL?.trim()
      : body.action === "challenge"
        ? process.env.CINEMA_CHALLENGE_URL?.trim()
        : "";

  if (!endpoint) {
    return NextResponse.json(
      { success: false, configured: false, error: `${body.action} action endpoint is not configured.` },
      { status: 503 }
    );
  }

  const headers: HeadersInit = { "Content-Type": "application/json" };
  const token = process.env.CINEMA_BACKEND_TOKEN?.trim();
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify(body.payload),
      cache: "no-store"
    });
    const text = await response.text();
    let data: unknown;
    try { data = JSON.parse(text); } catch { data = { success: response.ok, result: text }; }
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ success: false, error: "Cinema action request failed." }, { status: 502 });
  }
}
