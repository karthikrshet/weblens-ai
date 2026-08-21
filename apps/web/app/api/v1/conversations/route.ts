import { NextRequest, NextResponse } from "next/server";
import { conversationStore, websiteStore, ConversationEntity } from "@/lib/serverless-engine";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const website_id = body.website_id;

    const customBackend = process.env.BACKEND_API_URL;
    if (customBackend) {
      const res = await fetch(`${customBackend}/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }

    const website = websiteStore.get(website_id);
    const convId = "conv-" + Math.random().toString(36).substring(2, 11);
    const now = new Date().toISOString();

    const conversation: ConversationEntity = {
      id: convId,
      website_id,
      title: body.title || `Chat with ${website?.name || "Website"}`,
      created_at: now,
      updated_at: now,
      messages: [],
    };

    conversationStore.set(convId, conversation);
    return NextResponse.json(conversation);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Failed to create conversation";
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
