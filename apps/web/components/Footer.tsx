import Link from "next/link";
import { Shield, GitBranch, Cpu, Lock } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-[#070b12] py-12 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-white font-bold">
            <Cpu className="w-5 h-5 text-blue-400" />
            <span>WebLens AI</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Production-grade Agentic Website Intelligence & Exploration system. URL to deep grounded RAG with backend-enforced security boundaries.
          </p>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-cyan-400" />
            Security Defenses
          </h4>
          <ul className="space-y-2 text-xs">
            <li className="flex items-center gap-1.5 text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              SSRF & Private IP Blockers
            </li>
            <li className="flex items-center gap-1.5 text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Prompt Injection Isolation
            </li>
            <li className="flex items-center gap-1.5 text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Strict Redirect & Port Whitelist
            </li>
            <li className="flex items-center gap-1.5 text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Streaming Byte Cutoff (5MB)
            </li>
          </ul>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5 text-purple-400" />
            Architecture
          </h4>
          <ul className="space-y-2 text-xs">
            <li>Single Orchestrator Agent</li>
            <li>Hybrid BM25 + Dense RAG</li>
            <li>Deterministic Controlled Tools</li>
            <li>Heading-Aware Semantic Chunking</li>
          </ul>
        </div>

        <div>
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            Disclaimer & Policy
          </h4>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            WebLens analyzes publicly accessible web content. For high-stakes domains (healthcare, financial, legal), findings represent public website claims rather than certified professional advice.
          </p>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 pt-6 border-t border-slate-800/60 text-xs text-center text-slate-400">
        © {new Date().getFullYear()} WebLens AI • Built for AI Agent Engineering Excellence
      </div>
    </footer>
  );
}
