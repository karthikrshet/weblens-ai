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

  const website = websiteStore.get(id);
  if (!website) {
    return NextResponse.json({ detail: "Website profile not found" }, { status: 404 });
  }

  return NextResponse.json(website);
}
