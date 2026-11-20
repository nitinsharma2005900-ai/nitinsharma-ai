import React from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  Files,
  BarChart3,
  Brain,
  Code2,
  Settings as SettingsIcon,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'chat', label: 'AI Chat', icon: MessageSquare },
  { id: 'documents', label: 'Document Library', icon: Files },
  { id: 'analytics', label: 'Retrieval Analytics', icon: BarChart3 },
  { id: 'memory', label: 'Semantic Memory', icon: Brain },
  { id: 'api-docs', label: 'API Documentation', icon: Code2 },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="w-64 border-r border-white/5 p-4 flex flex-col justify-between glass-panel sticky top-16 h-[calc(100vh-4rem)]">
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-[10px] uppercase font-bold tracking-wider text-slate-500">
          Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-purple-600/20 text-cyan-300 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400"></span>
              )}
            </button>
          );
        })}
      </div>

      {/* Version badge */}
      <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-400 space-y-1">
        <div className="flex items-center justify-between font-mono text-[11px]">
          <span className="text-slate-400">RRF Fusion:</span>
          <span className="text-cyan-400 font-semibold">k=60</span>
        </div>
        <div className="flex items-center justify-between font-mono text-[11px]">
          <span className="text-slate-400">ReRank Model:</span>
          <span className="text-purple-400 font-semibold">v3.0</span>
        </div>
      </div>
    </aside>
  );
}
