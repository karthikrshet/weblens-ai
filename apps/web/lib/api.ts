/**
 * WebLens AI Client API SDK.
 */

export interface WebsiteResponse {
  id: string;
  url: string;
  canonical_url: string;
  domain: string;
  name?: string;
  website_type?: string;
  industry?: string;
  purpose?: string;
  target_audience?: string;
  summary?: string;
  confidence?: number;
  language?: string;
  categories: string[];
  products_or_services: string[];
  key_features: string[];
  key_pages: Array<{ url: string; title?: string; category?: string; relevance_score?: number }>;
  limitations?: string;
  created_at: string;
  updated_at: string;
  last_crawled_at?: string;
  page_count: number;
  chunk_count: number;
}

export interface SourceCitation {
  id?: string;
  url: string;
  title?: string;
  section?: string;
  chunk_id?: string;
  relevance_score: number;
  snippet?: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources: SourceCitation[];
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  website_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
}

export interface ToolExecutionRecord {
  id: string;
  run_id?: string;
  conversation_id?: string;
  tool_name: string;
  safe_input_summary: string;
  result_summary: string;
  status: "pending" | "running" | "success" | "failed" | "blocked";
  duration_ms: number;
  created_at: string;
}

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }
  return "/api/v1";
}

async function safeFetch(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (err: any) {
    if (err?.name === "TypeError" || (err?.message && err.message.toLowerCase().includes("failed to fetch"))) {
      throw new Error(
        "Unable to connect to the WebLens API backend. Please ensure the backend server is running and accessible (check NEXT_PUBLIC_API_URL in production)."
      );
    }
    throw err;
  }
}

export async function analyzeWebsite(url: string, forceRefresh: boolean = false): Promise<WebsiteResponse> {
  const apiBase = getApiBase();
  const res = await safeFetch(`${apiBase}/websites/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, force_refresh: forceRefresh }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(errorData.detail || `Server error (${res.status})`);
  }

  return res.json();
}

export async function getWebsite(id: string): Promise<WebsiteResponse> {
  const apiBase = getApiBase();
  const res = await safeFetch(`${apiBase}/websites/${id}`);
  if (!res.ok) throw new Error("Website not found");
  return res.json();
}

export async function createConversation(websiteId: string, title?: string): Promise<ConversationResponse> {
  const apiBase = getApiBase();
  const res = await safeFetch(`${apiBase}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ website_id: websiteId, title }),
  });
  if (!res.ok) throw new Error("Could not create conversation");
  return res.json();
}

export async function getConversation(id: string): Promise<ConversationResponse> {
  const apiBase = getApiBase();
  const res = await safeFetch(`${apiBase}/conversations/${id}`);
  if (!res.ok) throw new Error("Conversation not found");
  return res.json();
}

export async function sendMessage(conversationId: string, content: string): Promise<MessageResponse> {
  const apiBase = getApiBase();
  const res = await safeFetch(`${apiBase}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Message failed" }));
    throw new Error(err.detail || "Failed to send message");
  }
  return res.json();
}

export async function getConversationTelemetry(conversationId: string): Promise<ToolExecutionRecord[]> {
  const apiBase = getApiBase();
  try {
    const res = await safeFetch(`${apiBase}/conversations/${conversationId}/telemetry`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

