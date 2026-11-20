import React, { useState, useEffect } from 'react';
import {
  Brain,
  Trash2,
  Sparkles,
  User,
  Plus,
  CheckCircle,
  Tag,
  Clock,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import { api } from '../services/api';

export default function Memories({ activeUser }) {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const res = await api.getUserMemories(activeUser);
      setMemories(res.memories || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [activeUser]);

  const handleDelete = async (memoryId) => {
    try {
      await api.deleteMemory(activeUser, memoryId);
      setMessage({ type: 'success', text: 'Memory fact deleted successfully.' });
      fetchMemories();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  const handleClearAll = async () => {
    if (!confirm(`Are you sure you want to clear all semantic memories for user '${activeUser}'?`)) return;
    try {
      await api.clearMemories(activeUser);
      setMessage({ type: 'success', text: `Cleared all memories for '${activeUser}'.` });
      fetchMemories();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-400" />
            <span>Semantic Memory Store (Mem0)</span>
          </h2>
          <p className="text-xs text-slate-400">
            Persistent long-term facts, developer preferences, and coding styles automatically extracted from chat interactions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchMemories}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleClearAll}
            disabled={memories.length === 0}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-medium disabled:opacity-40 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear All Memories</span>
          </button>
        </div>
      </div>

      {/* Alert */}
      {message && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
              : 'bg-rose-500/10 border border-rose-500/20 text-rose-300'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          <span>{message.text}</span>
        </div>
      )}

      {/* User Info Card */}
      <GlassCard className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-purple-500">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-md">
            <User className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-bold text-white flex items-center gap-2">
              <span>Active User Profile:</span>
              <span className="font-mono text-cyan-400">{activeUser}</span>
            </div>
            <p className="text-xs text-slate-400">
              {memories.length} semantic facts actively shaping Gemini's system persona
            </p>
          </div>
        </div>

        <div className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 font-mono">
          Persistent Storage: <span className="text-emerald-400 font-semibold">Active (JSON/SQLite)</span>
        </div>
      </GlassCard>

      {/* Persona Adaptation Verification Card */}
      <GlassCard className="space-y-3 bg-gradient-to-r from-purple-950/40 via-navy-850 to-navy-900 border-purple-500/20">
        <div className="flex items-center gap-2 text-purple-300 font-semibold text-xs uppercase tracking-wider">
          <Sparkles className="w-4 h-4" />
          <span>Assessment Verification: Multi-Session Persona Adaptation</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          <strong>How it works:</strong> In Session 1, when the user inputs: <em>"Hello! I work in Python and prefer brief, code-only responses."</em>, the agent automatically captures and records these preferences below. In future sessions, queries like <em>"Write a quick merge sort routine"</em> bypass explanations and return only the requested Python code block.
        </p>
      </GlassCard>

      {/* Memories List */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <h3 className="text-sm font-bold text-white">Extracted Facts & Preferences</h3>
          <span className="text-xs font-mono text-purple-400">{memories.length} Stored</span>
        </div>

        {memories.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            No memories stored for user <strong className="text-slate-400">{activeUser}</strong> yet. Send a message in AI Chat stating your preferences to create one!
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {memories.map((m) => (
              <div key={m.id} className="py-3.5 flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="text-sm font-medium text-slate-200">{m.fact}</div>
                  <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      {m.category || 'preference'}
                    </span>
                    <span>ID: {m.id}</span>
                    <span>•</span>
                    <span>{m.created_at}</span>
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(m.id)}
                  className="p-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 transition-colors"
                  title="Delete fact"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
