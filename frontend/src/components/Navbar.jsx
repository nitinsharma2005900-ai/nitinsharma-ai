import React, { useEffect, useState } from 'react';
import { Shield, Sparkles, User, Activity, Moon, Sun } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar({ activeUser, setActiveUser, sessionId, setSessionId, isDark, setIsDark }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.getHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'offline' }));
    
    const interval = setInterval(() => {
      api.getHealth().then(setHealth).catch(() => setHealth({ status: 'offline' }));
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-white/5 px-6 flex items-center justify-between glass-panel sticky top-0 z-30">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base bg-gradient-to-r from-white via-slate-200 to-cyan-300 bg-clip-text text-transparent">
            Advanced RAG Agent
          </h1>
          <div className="flex items-center gap-2">
            <span className="text-[10px] tracking-wider uppercase font-semibold text-cyan-400">
              Context Compression & Semantic Memory
            </span>
          </div>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* System Health Pulse */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-rose-400'
            }`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500'
            }`}></span>
          </span>
          <span className="text-slate-300 font-mono text-[11px]">
            {health?.status === 'healthy' ? (health?.mode === 'offline_test' ? 'Offline Mode' : 'Online API') : 'Connecting...'}
          </span>
        </div>

        {/* User Selector */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-xl bg-white/5 border border-white/10 text-xs">
          <User className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">User:</span>
          <select
            value={activeUser}
            onChange={(e) => setActiveUser(e.target.value)}
            className="bg-transparent text-cyan-300 font-mono text-xs focus:outline-none cursor-pointer"
          >
            <option value="usr_99" className="bg-navy-900 text-white">usr_99 (Default Test)</option>
            <option value="usr_developer" className="bg-navy-900 text-white">usr_developer</option>
            <option value="usr_researcher" className="bg-navy-900 text-white">usr_researcher</option>
          </select>
        </div>

        {/* Dark/Light toggle */}
        <button
          onClick={() => setIsDark(!isDark)}
          className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:text-cyan-400 hover:bg-white/10 transition-colors"
          title="Toggle Theme"
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
}
