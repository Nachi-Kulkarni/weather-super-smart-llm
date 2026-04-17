import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const apiBaseUrl =
  process.env.RECOMMENDATION_API_URL ||
  process.env.NEXT_PUBLIC_RECOMMENDATION_API_URL ||
  "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const body = await request.text();

  const response = await fetch(`${apiBaseUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body,
    cache: "no-store",
  });

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") || "application/json",
    },
  });
}
