import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "WebLens AI API (Serverless & Edge Ready)",
    version: "0.1.0",
  });
}
