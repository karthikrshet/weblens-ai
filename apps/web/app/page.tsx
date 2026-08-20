"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Globe,
  ArrowRight,
  ShieldCheck,
  Search,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Layers,
  FileCode,
  Terminal,
  Activity,
} from "lucide-react";
import { analyzeWebsite } from "@/lib/api";

const PRESET_EXAMPLES = [
  { name: "SaaS Platform", url: "https://stripe.com", type: "saas" },
  { name: "E-Commerce Apparel", url: "https://nike.com", type: "ecommerce" },
  { name: "Education & FYP", url: "https://academy.codemyfyp.com", type: "education" },
  { name: "Clinical Healthcare", url: "https://mayoclinic.org", type: "healthcare" },
  { name: "Dev Documentation", url: "https://docs.python.org", type: "documentation" },
];

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusSteps, setStatusSteps] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setError(null);
    setLoading(true);
    setStatusSteps(["Validating destination and SSRF boundaries..."]);

    try {
      // Simulate live step transitions for UI responsiveness
      setTimeout(() => setStatusSteps((s) => [...s, "Fetching homepage & checking content density..."]), 300);
      setTimeout(() => setStatusSteps((s) => [...s, "Discovering high-value internal links..."]), 700);
      setTimeout(() => setStatusSteps((s) => [...s, "Extracting clean structural markdown & headings..."]), 1100);
      setTimeout(() => setStatusSteps((s) => [...s, "Classifying website domain & target audience..."]), 1500);
      setTimeout(() => setStatusSteps((s) => [...s, "Indexing semantic chunks into hybrid vector store..."]), 1900);

      const res = await analyzeWebsite(url);
      setStatusSteps((s) => [...s, "Analysis completed successfully! Redirecting..."]);
      setTimeout(() => {
        router.push(`/website/${res.id}`);
      }, 500);
    } catch (err: any) {
      setError(err.message || "Failed to analyze website. Please check the URL.");
      setLoading(false);
    }
  };

  return (
    <div className="relative overflow-hidden py-16 sm:py-24">
      {/* Background glowing glow orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-blue-600/15 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute top-1/3 left-1/3 w-[400px] h-[300px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-6">
          <Zap className="w-3.5 h-3.5" />
          Autonomous Website Intelligence & RAG
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6">
          Understand any website with an <br />
          <span className="gradient-text">Agentic Exploration System</span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-400 mb-10 leading-relaxed">
          Provide any public website URL. WebLens autonomously understands its purpose, classifies its domain, extracts structured intelligence, and lets you investigate deeper through grounded AI conversations.
        </p>

        {/* URL Input Form */}
        <form onSubmit={handleAnalyze} className="max-w-2xl mx-auto mb-6">
          <div className="flex flex-col sm:flex-row gap-2 p-2 rounded-2xl glass-panel focus-within:ring-2 focus-within:ring-blue-500/50 transition-all shadow-2xl">
            <div className="relative flex-1 flex items-center">
              <Globe className="absolute left-4 w-5 h-5 text-slate-500 pointer-events-none" />
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                disabled={loading}
                className="w-full pl-12 pr-4 py-3 bg-transparent text-white placeholder-slate-500 text-sm focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze Website
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Preset sample URLs */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-12">
          <span className="text-xs text-slate-400 mr-2">Try examples:</span>
          {PRESET_EXAMPLES.map((item) => (
            <button
              key={item.url}
              onClick={() => setUrl(item.url)}
              disabled={loading}
              className="px-3 py-1 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white transition-all font-mono"
            >
              {item.name}
            </button>
          ))}
        </div>

        {/* Live Progress Stage Stream */}
        {loading && (
          <div className="max-w-xl mx-auto mb-12 p-5 rounded-xl glass-card text-left text-xs font-mono border border-blue-500/30 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
              <span className="text-blue-400 font-semibold flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Agent Execution Pipeline
              </span>
              <span className="text-slate-400 animate-pulse">Running live...</span>
            </div>
            <div className="space-y-2">
              {statusSteps.map((step, idx) => (
                <div key={idx} className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="max-w-xl mx-auto mb-8 p-4 rounded-xl bg-red-950/50 border border-red-800 text-red-300 text-sm flex items-start gap-3 text-left">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Analysis Blocked or Failed</p>
              <p className="text-xs text-red-400/90 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Engineering Architecture Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left mt-16">
          <div className="p-6 rounded-2xl glass-card">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
              <Activity className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white mb-2">Agentic Orchestration</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Not a naive scraper. The agent acts as an autonomous reasoning layer with bounded tools (`search`, `crawl`, `profile`) to resolve user intents.
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-card">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white mb-2">Hybrid BM25 + Vector RAG</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Combines lexical keyword matching with dense semantic embeddings and heading-aware chunking for maximum retrieval precision.
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-card">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white mb-2">Defense-in-Depth Security</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Pre-connection SSRF DNS guards, link-local & cloud metadata blocks, prompt injection isolation, and hard 5MB streaming size limits.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
