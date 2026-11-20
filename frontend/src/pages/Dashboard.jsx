import React, { useEffect, useState } from 'react';
import { Files, MessageSquare, Brain, Zap, ArrowRight, ShieldCheck, Cpu, Database, Layers } from 'lucide-react';
import GlassCard from '../components/GlassCard';
import { api } from '../services/api';

export default function Dashboard({ setActiveTab, activeUser }) {
  const [stats, setStats] = useState({
    documents: 0,
    memories: 0,
    health: null,
  });

  useEffect(() => {
    Promise.all([
      api.getDocuments().catch(() => ({ total: 0 })),
      api.getUserMemories(activeUser).catch(() => ({ total_memories: 0 })),
      api.getHealth().catch(() => null),
    ]).then(([docsRes, memsRes, healthRes]) => {
      setStats({
        documents: docsRes.total || 0,
        memories: memsRes.total_memories || 0,
        health: healthRes,
      });
    });
  }, [activeUser]);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl p-8 glass-panel border border-cyan-500/20 bg-gradient-to-r from-navy-850 via-navy-800 to-navy-700">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 right-32 -mb-16 w-60 h-60 rounded-full bg-purple-500/10 blur-3xl pointer-events-none"></div>

        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold">
            <Cpu className="w-3.5 h-3.5" /> Production RAG Pipeline Active
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Advanced RAG Agent with Context Compression & Semantic Memory
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Eliminate boundary truncation and token inflation through hierarchical Parent-Child indexing,
            Dense-Sparse Reciprocal Rank Fusion, Cohere ReRank v3 context pruning, and persistent Mem0 persona adaptation.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => setActiveTab('chat')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium text-sm shadow-lg shadow-cyan-500/25 hover:opacity-95 transition-all"
            >
              <span>Start AI Chat</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-200 text-sm font-medium transition-all"
            >
              Upload Documents
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-cyan-300 text-sm font-medium transition-all"
            >
              Inspect Analytics
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <GlassCard hover onClick={() => setActiveTab('documents')} className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Indexed Docs</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
              <Files className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono">{stats.documents}</div>
          <div className="text-xs text-slate-400">PDF, TXT, DOCX supported</div>
        </GlassCard>

        <GlassCard hover onClick={() => setActiveTab('memory')} className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">User Memories</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Brain className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-purple-300 font-mono">{stats.memories}</div>
          <div className="text-xs text-slate-400">For profile: <span className="text-cyan-400">{activeUser}</span></div>
        </GlassCard>

        <GlassCard hover onClick={() => setActiveTab('analytics')} className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">RRF Smoothing</span>
            <div className="w-8 h-8 rounded-lg bg-pink-500/10 flex items-center justify-center text-pink-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-pink-300 font-mono">k = 60</div>
          <div className="text-xs text-slate-400">Dense + Sparse BM25 Fusion</div>
        </GlassCard>

        <GlassCard hover onClick={() => setActiveTab('chat')} className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">ReRank Top N</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-emerald-300 font-mono">5 docs</div>
          <div className="text-xs text-slate-400">From 20 candidate parents</div>
        </GlassCard>
      </div>

      {/* RAG Pipeline Architectural Blueprint */}
      <GlassCard className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">Advanced RAG Pipeline Blueprint</h3>
            <p className="text-xs text-slate-400">Hierarchical multi-stage flow connecting retrieval, compression, and generation</p>
          </div>
          <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono">
            End-to-End Orchestrated
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Stage 1 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
            <div className="text-xs font-bold text-cyan-400 font-mono">STAGE 01</div>
            <div className="text-sm font-semibold text-white">Hierarchical Ingestion</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Splits files into ~1000 char parent chunks & ~200 char child chunks with boundary preservation.
            </p>
          </div>

          {/* Stage 2 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
            <div className="text-xs font-bold text-purple-400 font-mono">STAGE 02</div>
            <div className="text-sm font-semibold text-white">Hybrid Retrieval</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Executes dense vector search and Okapi BM25 keyword search, fused via Reciprocal Rank Fusion.
            </p>
          </div>

          {/* Stage 3 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
            <div className="text-xs font-bold text-pink-400 font-mono">STAGE 03</div>
            <div className="text-sm font-semibold text-white">Parent Resolution</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Maps matched child chunks to original parent documents, retrieving complete context nodes.
            </p>
          </div>

          {/* Stage 4 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
            <div className="text-xs font-bold text-amber-400 font-mono">STAGE 04</div>
            <div className="text-sm font-semibold text-white">Cohere ReRank</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Re-evaluates top 20 candidate parents, drops chunks below threshold, and compresses top 5 contexts.
            </p>
          </div>

          {/* Stage 5 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
            <div className="text-xs font-bold text-emerald-400 font-mono">STAGE 05</div>
            <div className="text-sm font-semibold text-white">Gemini + Memory</div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Injects Mem0 user preferences into system prompt, generating cited responses with telemetry.
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
