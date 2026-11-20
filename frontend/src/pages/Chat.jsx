import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Trash2,
  Sparkles,
  User,
  Bot,
  Layers,
  ChevronDown,
  ChevronRight,
  BookOpen,
  PlusCircle,
  Clock,
  Zap,
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import TelemetryBadge from '../components/TelemetryBadge';
import { api } from '../services/api';

export default function Chat({ activeUser, sessionId, setSessionId }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am your **Advanced RAG Agent** equipped with Context Compression & Semantic Memory.\n\nYou can ask me questions about your uploaded documents, or share your programming language and response style preferences.',
      citations: [],
      sources: [],
      telemetry: null,
      memory: null,
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim() || isLoading) return;

    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: query,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const response = await api.chat({
        query,
        userId: activeUser,
        sessionId,
      });

      const assistantMsg = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        citations: response.citations || [],
        sources: response.sources || [],
        telemetry: response.telemetry,
        memory: response.memory,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Error**: ${err.message}`,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCitations = (msgId) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content:
          'Chat history cleared. How can I assist you with your documents or research?',
        citations: [],
        sources: [],
        telemetry: null,
      },
    ]);
  };

  const startNewSession = () => {
    const nextSession = `session_${Math.floor(100 + Math.random() * 900)}`;
    setSessionId(nextSession);
    setMessages([
      {
        id: `welcome_${nextSession}`,
        role: 'assistant',
        content: `Started new chat session **${nextSession}** for user **${activeUser}**. Your semantic memory profile remains active!`,
        citations: [],
        sources: [],
      },
    ]);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col gap-4">
      {/* Top Session & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Current Session:</span>
          <span className="px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-semibold">
            {sessionId}
          </span>
          <button
            onClick={startNewSession}
            className="flex items-center gap-1 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span>New Session</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 hover:bg-rose-500/20 hover:text-rose-300 border border-white/10 text-xs text-slate-400 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Preset verification quick prompts */}
      <div className="flex flex-wrap items-center gap-2 px-2 text-xs">
        <span className="text-slate-500 font-semibold text-[11px] uppercase tracking-wider">Test Shortcuts:</span>
        <button
          onClick={() => handleSend("Hello! I work in Python and prefer brief, code-only responses.")}
          className="px-2.5 py-1 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 font-mono text-[11px] transition-colors"
        >
          Session 1: "Work in Python & brief code-only"
        </button>
        <button
          onClick={() => handleSend("Write a quick merge sort routine.")}
          className="px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 font-mono text-[11px] transition-colors"
        >
          Session 2: "Write a quick merge sort routine."
        </button>
      </div>

      {/* Messages Scroll Area */}
      <GlassCard className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-4 space-y-3 ${
                  isUser
                    ? 'bg-gradient-to-r from-cyan-600 to-cyan-700 text-white shadow-lg shadow-cyan-600/15'
                    : 'bg-navy-800/90 border border-white/10 text-slate-200'
                }`}
              >
                {/* Message Body */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {msg.content}
                </div>

                {/* Sources & Citations Accordion */}
                {!isUser && msg.citations && msg.citations.length > 0 && (
                  <div className="pt-2 border-t border-white/5 space-y-2">
                    <button
                      onClick={() => toggleCitations(msg.id)}
                      className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>{msg.citations.length} Verified Sources Cited</span>
                      {expandedCitations[msg.id] ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedCitations[msg.id] && (
                      <div className="space-y-2 pt-1 animate-fadeIn">
                        {msg.citations.map((c, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs space-y-1"
                          >
                            <div className="flex items-center justify-between text-[11px] font-mono">
                              <span className="text-cyan-300 font-semibold">{c.document_name}</span>
                              <span className="text-purple-300">Score: {c.relevance_score.toFixed(2)}</span>
                            </div>
                            <div className="text-[10px] text-slate-400 font-mono">Chunk: {c.chunk_id}</div>
                            <div className="text-xs text-slate-300 italic">"{c.snippet}"</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Telemetry Footer */}
                {!isUser && msg.telemetry && (
                  <div className="pt-2 border-t border-white/5">
                    <TelemetryBadge telemetry={msg.telemetry} />
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-cyan-400" />
                </div>
              )}
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3.5 justify-start animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="rounded-2xl p-4 bg-navy-800/90 border border-white/10 text-xs text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-bounce [animation-delay:0.4s]"></span>
              <span>Running Hybrid Retrieval & Cohere ReRank...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </GlassCard>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-3 glass-panel p-2.5 rounded-2xl border border-white/10 focus-within:border-cyan-500/50 transition-colors"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={`Ask about documents or state preferences as ${activeUser}...`}
          disabled={isLoading}
          className="flex-1 bg-transparent px-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={isLoading || !inputQuery.trim()}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium text-sm flex items-center gap-2 hover:opacity-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-cyan-500/20 transition-all"
        >
          <span>Send</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
