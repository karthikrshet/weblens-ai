"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Send,
  Globe,
  Bot,
  User,
  ExternalLink,
  Activity,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  ChevronRight,
  Shield,
  Layers,
  ArrowLeft,
} from "lucide-react";
import {
  getConversation,
  sendMessage,
  getConversationTelemetry,
  ConversationResponse,
  MessageResponse,
  ToolExecutionRecord,
} from "@/lib/api";

const PRESET_QUESTIONS = [
  "What products and services do they sell?",
  "Tell me more about their pricing or plans.",
  "Who is their primary target audience?",
  "What is the company's core mission and purpose?",
];

export default function ChatPage() {
  const params = useParams();
  const conversationId = params.id as string;

  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [telemetry, setTelemetry] = useState<ToolExecutionRecord[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showTelemetryDrawer, setShowTelemetryDrawer] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!conversationId) return;
    Promise.all([
      getConversation(conversationId),
      getConversationTelemetry(conversationId),
    ])
      .then(([convData, telemData]) => {
        setConversation(convData);
        setMessages(convData.messages || []);
        setTelemetry(telemData || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || sending) return;

    setInput("");
    setSending(true);

    // Optimistic user message append
    const tempUserMsg: MessageResponse = {
      id: "temp-" + Date.now(),
      conversation_id: conversationId,
      role: "user",
      content: text,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const assistantMsg = await sendMessage(conversationId, text);
      setMessages((prev) => [...prev.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, assistantMsg]);
      
      // Refresh telemetry
      const updatedTelem = await getConversationTelemetry(conversationId);
      setTelemetry(updatedTelem);
    } catch (err: any) {
      alert(err.message || "Failed to send message.");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-slate-400 text-sm font-mono">Connecting to Agent RAG Session...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col h-[calc(100vh-5rem)]">
      {/* Top Session Bar */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          {conversation && (
            <Link
              href={`/website/${conversation.website_id}`}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
          )}
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-400" />
              {conversation?.title || "Website Investigation Session"}
            </h1>
            <p className="text-xs text-slate-400">Grounded Multi-Turn Agent Q&A with Citation Tracking</p>
          </div>
        </div>

        <button
          onClick={() => setShowTelemetryDrawer(!showTelemetryDrawer)}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 border transition-all ${
            showTelemetryDrawer
              ? "bg-blue-500/15 border-blue-500/30 text-blue-400"
              : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Agent Activity ({telemetry.length})
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex gap-6 overflow-hidden py-4">
        {/* Chat Stream Area */}
        <div className="flex-1 flex flex-col justify-between overflow-hidden glass-panel rounded-2xl border border-slate-800 p-4">
          <div className="flex-1 overflow-y-auto space-y-6 pr-2">
            {messages.length === 0 && (
              <div className="text-center py-16 text-slate-400">
                <Sparkles className="w-10 h-10 text-blue-400/80 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-white mb-1">Grounded Website Intelligence Ready</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mb-6">
                  Ask anything about the website. The agent will retrieve evidence and cite the exact source pages.
                </p>

                {/* Preset Suggestions */}
                <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
                  {PRESET_QUESTIONS.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(q)}
                      className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white text-left transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 text-sm ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center flex-shrink-0 text-blue-400 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-2xl space-y-3 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div
                    className={`p-4 rounded-2xl ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-none leading-relaxed"
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-xs sm:text-sm">{msg.content}</p>
                  </div>

                  {/* Grounded Source Citations */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                      <p className="text-[10px] font-mono font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        Grounded Sources ({msg.sources.length})
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((src, sIdx) => (
                          <a
                            key={sIdx}
                            href={src.url}
                            target="_blank"
                            rel="noreferrer"
                            className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-[11px] text-slate-300 hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                          >
                            <span className="font-medium truncate max-w-[180px]">
                              {src.title || src.section || src.url}
                            </span>
                            <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center flex-shrink-0 text-slate-300 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex gap-3 text-sm items-center text-slate-400 animate-pulse">
                <div className="w-8 h-8 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center flex-shrink-0 text-blue-400">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs font-mono">
                  Agent reasoning & retrieving evidence...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="mt-4 pt-3 border-t border-slate-800/80 flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a deeper question about this website..."
              disabled={sending}
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-xs sm:text-sm flex items-center gap-1.5 transition-all shadow-md shadow-blue-600/20"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
        </div>

        {/* Right Telemetry Drawer */}
        {showTelemetryDrawer && (
          <div className="w-80 glass-panel rounded-2xl border border-slate-800 p-4 flex flex-col overflow-hidden animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-cyan-400" />
                Agent Activity Trace
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                SAFE TELEMETRY
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 text-xs">
              {telemetry.length === 0 ? (
                <p className="text-slate-500 text-xs text-center py-10">No tool actions executed yet.</p>
              ) : (
                telemetry.map((exec) => (
                  <div
                    key={exec.id}
                    className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/90 space-y-1 font-mono text-[11px]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-blue-400">→ {exec.tool_name}()</span>
                      <span className="text-[10px] text-slate-400">{exec.duration_ms}ms</span>
                    </div>
                    <p className="text-slate-400 text-[10px] truncate">{exec.safe_input_summary}</p>
                    <div className="flex items-center gap-1.5 text-slate-300 pt-0.5">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                      <span className="truncate text-[10px]">{exec.result_summary}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
