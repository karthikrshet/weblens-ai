import { NextRequest, NextResponse } from "next/server";
import { websiteStore } from "@/lib/serverless-engine";

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const { id } = params;

  const customBackend = process.env.BACKEND_API_URL;
  if (customBackend) {
    const res = await fetch(`${customBackend}/websites/${id}`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  }

  let website = websiteStore.get(id);
  if (!website) {
    try {
      const decodedUrl = Buffer.from(id, "base64url").toString("utf-8");
      if (decodedUrl.startsWith("http://") || decodedUrl.startsWith("https://")) {
        const { ingestWebsite } = await import("@/lib/serverless-engine");
        website = await ingestWebsite(decodedUrl);
      }
    } catch {}
  }

  if (!website) {
    return NextResponse.json({ detail: "Website profile not found" }, { status: 404 });
  }

  return NextResponse.json(website);
}
