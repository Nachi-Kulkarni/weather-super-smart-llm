import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const apiBaseUrl =
  process.env.RECOMMENDATION_API_URL ||
  process.env.NEXT_PUBLIC_RECOMMENDATION_API_URL ||
  "http://127.0.0.1:8000";

/**
 * Proxies NDJSON from FastAPI `/chat/stream` for token + tool/reasoning streaming.
 */
export async function POST(request: NextRequest) {
  const body = await request.text();

  const response = await fetch(`${apiBaseUrl}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body,
    cache: "no-store",
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: {
      "Content-Type": "application/x-ndjson",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
