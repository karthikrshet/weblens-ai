import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const customBackend = process.env.BACKEND_API_URL;
  if (customBackend) {
    const res = await fetch(`${customBackend}/conversations/${params.id}/telemetry`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  }

  const now = new Date().toISOString();
  return NextResponse.json([
    {
      id: "tel-1",
      conversation_id: params.id,
      tool_name: "search_website",
      safe_input_summary: "hybrid_search(query, top_k=4)",
      result_summary: "Found relevant heading-aware passages from public website evidence",
      status: "success",
      duration_ms: 64.2,
      created_at: now,
    },
  ]);
}
