"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Globe,
  ExternalLink,
  MessageSquare,
  Layers,
  Sparkles,
  Target,
  Briefcase,
  CheckCircle,
  AlertCircle,
  FileText,
  Clock,
  ArrowRight,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import { getWebsite, WebsiteResponse, createConversation } from "@/lib/api";

export default function WebsiteDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const websiteId = params.id as string;

  const [website, setWebsite] = useState<WebsiteResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startingChat, setStartingChat] = useState(false);

  useEffect(() => {
    if (!websiteId) return;
    getWebsite(websiteId)
      .then((data) => {
        setWebsite(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load website profile.");
        setLoading(false);
      });
  }, [websiteId]);

  const handleStartChat = async () => {
    if (!website) return;
    setStartingChat(true);
    try {
      const conv = await createConversation(website.id, `Chat: ${website.name || website.domain}`);
      router.push(`/chat/${conv.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to start conversation.");
      setStartingChat(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-slate-400 text-sm font-mono">Loading structured website intelligence...</p>
      </div>
    );
  }

  if (error || !website) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Website Profile Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">{error || "Could not retrieve the requested website data."}</p>
        <Link href="/" className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium">
          Analyze Another Website
        </Link>
      </div>
    );
  }

  const confidencePct = Math.round((website.confidence || 0.85) * 100);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Top Header Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl mb-8 border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {website.name || website.domain}
              </h1>
              <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/30">
                {website.website_type || "other"}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-400">
              <a
                href={website.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 hover:text-cyan-400 transition-colors"
              >
                <Globe className="w-3.5 h-3.5" />
                {website.canonical_url || website.url}
                <ExternalLink className="w-3 h-3 ml-0.5 opacity-70" />
              </a>
              <span className="text-slate-700">•</span>
              <span className="flex items-center gap-1 text-slate-400">
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                {website.page_count} Pages Indexed
              </span>
              <span className="text-slate-700">•</span>
              <span className="flex items-center gap-1 text-slate-400">
                <Layers className="w-3.5 h-3.5 text-purple-400" />
                {website.chunk_count} RAG Chunks
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            {/* Confidence Score Pill */}
            <div className="px-4 py-2.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3">
              <div>
                <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Classification Confidence</p>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400 rounded-full"
                      style={{ width: `${confidencePct}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-white font-mono">{confidencePct}%</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleStartChat}
              disabled={startingChat}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white text-sm font-semibold flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all"
            >
              {startingChat ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <MessageSquare className="w-4 h-4" />
                  Investigate with Agent
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Limitations / Healthcare Disclaimer Box */}
      {website.limitations && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/80 text-amber-300 text-xs mb-8 flex items-start gap-3">
          <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-200">Domain Note & Attributed Claims</p>
            <p className="text-amber-400/90 mt-0.5 leading-relaxed">{website.limitations}</p>
          </div>
        </div>
      )}

      {/* Grid: Overview & Capabilities */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Left 2 Cols: Summary, Purpose & Audience */}
        <div className="lg:col-span-2 space-y-6">
          {/* Grounded Summary */}
          <div className="p-6 rounded-2xl glass-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              Grounded Overview
            </h2>
            <p className="text-sm text-slate-200 leading-relaxed font-normal">
              {website.summary || "No overview available."}
            </p>
          </div>

          {/* Purpose & Target Audience */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl glass-card">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Target className="w-4 h-4 text-cyan-400" />
                Primary Purpose
              </h3>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {website.purpose || "Information dissemination and digital operations."}
              </p>
            </div>

            <div className="p-5 rounded-xl glass-card">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-emerald-400" />
                Target Audience
              </h3>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {website.target_audience || "General digital consumers and businesses."}
              </p>
            </div>
          </div>

          {/* Products / Services & Key Features */}
          <div className="p-6 rounded-2xl glass-card space-y-6">
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Key Offerings & Capabilities
              </h3>
              <div className="flex flex-wrap gap-2">
                {(website.products_or_services?.length ? website.products_or_services : ["Core Platform Services"]).map(
                  (item, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-200 flex items-center gap-1.5"
                    >
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                      {item}
                    </span>
                  )
                )}
              </div>
            </div>

            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Identified Categories & Taxonomies
              </h3>
              <div className="flex flex-wrap gap-2">
                {(website.categories?.length ? website.categories : ["Technology"]).map((cat, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded-md bg-blue-950/40 border border-blue-800/60 text-xs text-blue-300 font-mono"
                  >
                    #{cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Discovered Important Pages & Quick Action */}
        <div className="space-y-6">
          <div className="p-6 rounded-2xl glass-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              Discovered Key Pages
            </h2>

            <div className="space-y-3">
              {(website.key_pages?.length ? website.key_pages : [{ url: "/", title: "Homepage", category: "general" }]).map(
                (p, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-colors text-xs"
                  >
                    <div className="flex items-center justify-between font-medium text-slate-200 mb-1">
                      <span className="truncate">{p.title || p.url}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-mono uppercase">
                        {p.category || "page"}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 font-mono truncate">{p.url}</p>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-900/30 to-purple-900/20 border border-blue-800/40 text-center">
            <h3 className="text-sm font-bold text-white mb-2">Ready to Explore Deeper?</h3>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Ask deep questions about pricing, features, technical stack, or business model. The agent will retrieve grounded evidence on demand.
            </p>
            <button
              onClick={handleStartChat}
              disabled={startingChat}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 transition-all"
            >
              Start Investigation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
