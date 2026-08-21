import { NextRequest, NextResponse } from "next/server";
import { conversationStore, websiteStore, ConversationEntity, ingestWebsite } from "@/lib/serverless-engine";

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const conversationId = params.id;

    const customBackend = process.env.BACKEND_API_URL;
    if (customBackend) {
      const res = await fetch(`${customBackend}/conversations/${conversationId}`);
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }

    let conv = conversationStore.get(conversationId);

    // Auto-heal / reconstruct conversation on serverless cold starts
    if (!conv) {
      const rawId = conversationId.replace(/^conv-/, "");
      let website = websiteStore.get(rawId);

      // If website not found in memory, attempt URL decoding if base64url encoded
      if (!website) {
        try {
          const decodedUrl = Buffer.from(rawId, "base64url").toString("utf-8");
          if (decodedUrl.startsWith("http://") || decodedUrl.startsWith("https://")) {
            website = await ingestWebsite(decodedUrl);
          }
        } catch {
          // ignore decoding errors
        }
      }

      const now = new Date().toISOString();
      conv = {
        id: conversationId,
        website_id: rawId,
        title: `Chat with ${website?.name || "Website"}`,
        created_at: now,
        updated_at: now,
        messages: [],
      };
      conversationStore.set(conversationId, conv);
    }

    return NextResponse.json(conv);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Failed to load conversation";
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
