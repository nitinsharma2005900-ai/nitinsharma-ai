import React, { useState } from 'react';
import {
  Search,
  Layers,
  BarChart2,
  FileCheck,
  Zap,
  TrendingDown,
  ArrowRight,
  Minimize2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';
import GlassCard from '../components/GlassCard';
import { api } from '../services/api';

export default function Analytics({ activeUser }) {
  const [query, setQuery] = useState('hybrid search parent document retrieval BM25');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInspect = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await api.inspectRetrieval(query, activeUser);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const latencyChartData = data?.telemetry
    ? [
        { name: 'Retrieval (Hybrid)', ms: data.telemetry.retrieval_latency_ms, fill: '#06b6d4' },
        { name: 'ReRank (Cohere)', ms: data.telemetry.rerank_latency_ms, fill: '#8b5cf6' },
        { name: 'Total Overhead', ms: data.telemetry.total_latency_ms, fill: '#10b981' },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Retrieval & Context Compression Analytics</h2>
        <p className="text-xs text-slate-400">
          Inspect stage-by-stage transformations: Dense embeddings vs. Okapi BM25, Reciprocal Rank Fusion, and Cohere ReRank token pruning.
        </p>
      </div>

      {/* Query Inspection Bar */}
      <form onSubmit={handleInspect} className="flex gap-3">
        <div className="flex-1 glass-panel px-4 py-2.5 rounded-xl border border-white/10 flex items-center gap-3">
          <Search className="w-4 h-4 text-cyan-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter query to trace across retrieval indices..."
            className="w-full bg-transparent text-sm text-white focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium text-sm flex items-center gap-2 hover:opacity-95 disabled:opacity-50 transition-all"
        >
          <span>{loading ? 'Inspecting...' : 'Trace Pipeline'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {/* Latency Visualization */}
      {data?.telemetry && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <GlassCard className="space-y-2">
            <span className="text-xs text-slate-400 font-mono">Retrieval Stage</span>
            <div className="text-2xl font-bold text-cyan-400 font-mono">
              {data.telemetry.retrieval_latency_ms.toFixed(2)} ms
            </div>
            <p className="text-[11px] text-slate-400">Dense search + BM25 + RRF</p>
          </GlassCard>

          <GlassCard className="space-y-2">
            <span className="text-xs text-slate-400 font-mono">ReRank & Compression</span>
            <div className="text-2xl font-bold text-purple-400 font-mono">
              {data.telemetry.rerank_latency_ms.toFixed(2)} ms
            </div>
            <p className="text-[11px] text-slate-400">Cohere ReRank v3.0 top-5 selection</p>
          </GlassCard>

          <GlassCard className="space-y-2">
            <span className="text-xs text-slate-400 font-mono">Total Overhead</span>
            <div className="text-2xl font-bold text-emerald-400 font-mono">
              {data.telemetry.total_latency_ms.toFixed(2)} ms
            </div>
            <p className="text-[11px] text-slate-400">Roundtrip pipeline processing</p>
          </GlassCard>
        </div>
      )}

      {/* Latency Chart */}
      {latencyChartData.length > 0 && (
        <GlassCard className="space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400" />
            <span>Execution Latency Breakdown (ms)</span>
          </h3>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyChartData} layout="vertical" margin={{ left: 30, right: 30 }}>
                <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#64748b"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  width={140}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1120', borderColor: '#334155', borderRadius: 8, color: '#fff' }}
                />
                <Bar dataKey="ms" radius={[0, 8, 8, 0]}>
                  {latencyChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Multi-Index Results Comparison */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Dense Search Top 5 */}
          <GlassCard className="space-y-3">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <span className="text-sm font-bold text-cyan-400 flex items-center gap-1.5">
                <Layers className="w-4 h-4" /> Dense Vector Search (Cohere / Qdrant)
              </span>
              <span className="text-xs font-mono text-slate-400">{data.dense_results.length} results</span>
            </div>
            <div className="space-y-2">
              {data.dense_results.map((item, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs space-y-1">
                  <div className="flex justify-between font-mono text-[11px]">
                    <span className="text-slate-300">#{item.rank} {item.doc_name}</span>
                    <span className="text-cyan-300">Cos Sim: {item.score.toFixed(4)}</span>
                  </div>
                  <div className="text-slate-400 text-[11px] italic">"{item.text}..."</div>
                </div>
              ))}
              {data.dense_results.length === 0 && (
                <div className="text-slate-500 text-xs py-4 text-center">No dense matches</div>
              )}
            </div>
          </GlassCard>

          {/* Sparse BM25 Top 5 */}
          <GlassCard className="space-y-3">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <span className="text-sm font-bold text-purple-400 flex items-center gap-1.5">
                <BarChart2 className="w-4 h-4" /> Sparse Lexical Search (Okapi BM25)
              </span>
              <span className="text-xs font-mono text-slate-400">{data.sparse_results.length} results</span>
            </div>
            <div className="space-y-2">
              {data.sparse_results.map((item, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs space-y-1">
                  <div className="flex justify-between font-mono text-[11px]">
                    <span className="text-slate-300">#{item.rank} {item.doc_name}</span>
                    <span className="text-purple-300">BM25 Score: {item.score.toFixed(4)}</span>
                  </div>
                  <div className="text-slate-400 text-[11px] italic">"{item.text}..."</div>
                </div>
              ))}
              {data.sparse_results.length === 0 && (
                <div className="text-slate-500 text-xs py-4 text-center">No BM25 matches</div>
              )}
            </div>
          </GlassCard>
        </div>
      )}

      {/* RRF Fused & Cohere ReRank */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* RRF Fused */}
          <GlassCard className="space-y-3">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <span className="text-sm font-bold text-pink-400">Reciprocal Rank Fusion (RRF k=60)</span>
              <span className="text-xs font-mono text-slate-400">{data.rrf_fused.length} fused</span>
            </div>
            <div className="space-y-2">
              {data.rrf_fused.map((item, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs space-y-1">
                  <div className="flex justify-between font-mono text-[11px]">
                    <span className="text-slate-300">#{idx + 1} {item.doc_name}</span>
                    <span className="text-pink-300 font-bold">RRF: {item.rrf_score.toFixed(5)}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    Dense Rank: {item.dense_rank || 'N/A'} | Sparse Rank: {item.sparse_rank || 'N/A'}
                  </div>
                  <div className="text-slate-400 text-[11px] italic">"{item.text}..."</div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Top 5 Cohere ReRank with Context Compression */}
          <GlassCard className="space-y-3">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <span className="text-sm font-bold text-emerald-400">Top 5 ReRanked & Compressed Documents</span>
              <span className="text-xs font-mono text-emerald-300 font-semibold">{data.reranked_top5.length} Passed</span>
            </div>
            <div className="space-y-2">
              {data.reranked_top5.map((item, idx) => {
                const reduction = Math.max(0, Math.round((1 - item.compressed_len / item.original_len) * 100));
                return (
                  <div key={idx} className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs space-y-1.5">
                    <div className="flex justify-between font-mono text-[11px]">
                      <span className="text-slate-200 font-semibold">#{idx + 1} {item.doc_name}</span>
                      <span className="text-emerald-300 font-bold">Relevance: {item.relevance_score.toFixed(4)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-cyan-300">
                      <span>Orig: {item.original_len} chars</span>
                      <span>→</span>
                      <span>Compressed: {item.compressed_len} chars</span>
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                        -{reduction}% tokens
                      </span>
                    </div>
                    <div className="text-slate-300 text-[11px] leading-relaxed bg-black/20 p-2 rounded">
                      {item.compressed_text}
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
