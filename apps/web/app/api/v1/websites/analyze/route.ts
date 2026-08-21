import { NextRequest, NextResponse } from "next/server";
import { ingestWebsite, websiteStore } from "@/lib/serverless-engine";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const url = body.url?.trim();
    if (!url) {
      return NextResponse.json({ detail: "URL is required" }, { status: 400 });
    }

    // Check if custom backend is configured
    const customBackend = process.env.BACKEND_API_URL;
    if (customBackend) {
      const res = await fetch(`${customBackend}/websites/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }

    // Run Serverless Ingestion Engine
    const website = await ingestWebsite(url);
    return NextResponse.json(website);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Website analysis failed";
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
