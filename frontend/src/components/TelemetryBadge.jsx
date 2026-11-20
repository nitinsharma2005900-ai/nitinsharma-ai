import React from 'react';
import { Clock, Zap, Search, Layers, Cpu } from 'lucide-react';

export default function TelemetryBadge({ telemetry, showDetails = true }) {
  if (!telemetry) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
      {/* Total Latency Pill */}
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
        <Zap className="w-3.5 h-3.5 text-emerald-400" />
        <span>{telemetry.total_latency_ms.toFixed(1)}ms total</span>
      </div>

      {showDetails && (
        <>
          {/* Retrieval */}
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
            <Search className="w-3 h-3 text-cyan-400" />
            <span>Ret: {telemetry.retrieval_latency_ms.toFixed(1)}ms</span>
          </div>

          {/* ReRank */}
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300">
            <Layers className="w-3 h-3 text-purple-400" />
            <span>Rerank: {telemetry.rerank_latency_ms.toFixed(1)}ms</span>
          </div>

          {/* Generation */}
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-pink-500/10 border border-pink-500/20 text-pink-300">
            <Cpu className="w-3 h-3 text-pink-400" />
            <span>Gen: {telemetry.generation_latency_ms.toFixed(1)}ms</span>
          </div>
        </>
      )}
    </div>
  );
}
