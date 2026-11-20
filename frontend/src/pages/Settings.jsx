import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Key, Sliders, Shield, Database, Cpu, CheckCircle, AlertTriangle } from 'lucide-react';
import GlassCard from '../components/GlassCard';
import { api } from '../services/api';

export default function Settings() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => null);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-cyan-400" />
          <span>System Settings & Configuration</span>
        </h2>
        <p className="text-xs text-slate-400">
          Inspect API connection status, pipeline hyperparameters, and runtime storage configurations.
        </p>
      </div>

      {/* API Keys & Services Status */}
      <GlassCard className="space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Key className="w-4 h-4 text-cyan-400" />
          <span>API Services & Authentication Status</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Google Gemini */}
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-white">Google Gemini API</div>
              <div className="text-[11px] text-slate-400 font-mono">Model: gemini-1.5-flash</div>
            </div>
            <span
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-medium ${
                health?.configuration?.gemini_api_configured
                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
              }`}
            >
              {health?.configuration?.gemini_api_configured ? 'Connected' : 'Offline / Local Fallback'}
            </span>
          </div>

          {/* Cohere API */}
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-white">Cohere API</div>
              <div className="text-[11px] text-slate-400 font-mono">Embed & ReRank v3.0</div>
            </div>
            <span
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-medium ${
                health?.configuration?.cohere_api_configured
                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
              }`}
            >
              {health?.configuration?.cohere_api_configured ? 'Connected' : 'Offline / Local Fallback'}
            </span>
          </div>

          {/* Mem0 */}
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-white">Mem0 Semantic Memory</div>
              <div className="text-[11px] text-slate-400 font-mono">Persistent User Facts</div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              Active (Local Disk/Cloud)
            </span>
          </div>

          {/* Qdrant */}
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-white">Qdrant Vector Database</div>
              <div className="text-[11px] text-slate-400 font-mono">Local Persistent Store</div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              Active (Persistent JSON/Vector DB)
            </span>
          </div>
        </div>
      </GlassCard>

      {/* RAG Hyperparameters */}
      <GlassCard className="space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span>RAG Pipeline Hyperparameters</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-slate-400">Parent Chunk Size:</span>
            <div className="text-lg font-bold text-cyan-300">1000 chars</div>
            <span className="text-[10px] text-slate-500 block">Overlap: 100 chars</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-slate-400">Child Chunk Size:</span>
            <div className="text-lg font-bold text-purple-300">200 chars</div>
            <span className="text-[10px] text-slate-500 block">Overlap: 30 chars</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-slate-400">RRF Smoothing Constant:</span>
            <div className="text-lg font-bold text-pink-300">k = 60</div>
            <span className="text-[10px] text-slate-500 block">Reciprocal rank fusion</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-slate-400">Top Candidates Retrieved:</span>
            <div className="text-lg font-bold text-amber-300">20 chunks</div>
            <span className="text-[10px] text-slate-500 block">Sent to Cohere ReRank</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-slate-400">Top N Filtered (Prompt):</span>
            <div className="text-lg font-bold text-emerald-300">5 documents</div>
            <span className="text-[10px] text-slate-500 block">Compressed context</span>
          </div>

          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1">
            <span className="text-slate-400">Relevance Score Threshold:</span>
            <div className="text-lg font-bold text-cyan-300">0.25</div>
            <span className="text-[10px] text-slate-500 block">Pruning below threshold</span>
          </div>
        </div>
      </GlassCard>

      {/* Security & Secrets Note */}
      <GlassCard className="space-y-2 border-l-4 border-l-cyan-500">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
          <Shield className="w-4 h-4" />
          <span>Security & Secrets Isolation</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          All API credentials are isolated in the root or backend <code className="text-cyan-300 font-mono">.env</code> file. The repository includes a clean <code className="text-cyan-300 font-mono">.env.example</code> template, and <code className="text-cyan-300 font-mono">.gitignore</code> strictly blocks secrets from ever being checked into version control.
        </p>
      </GlassCard>
    </div>
  );
}
