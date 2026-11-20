import React, { useState } from 'react';
import { Code2, Copy, Check, Terminal, ExternalLink } from 'lucide-react';
import GlassCard from '../components/GlassCard';

const ENDPOINTS = [
  {
    method: 'POST',
    path: '/api/chat',
    title: 'Execute RAG Chat Pipeline',
    desc: 'Runs full RAG pipeline: Hybrid Search, Parent Document retrieval, Cohere ReRank, Mem0 Semantic Memory, and Gemini generation with real latency telemetry.',
    curl: `curl -X POST http://localhost:8000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Explain how hybrid search and parent document retrieval eliminate chunk boundary truncation.",
    "user_id": "usr_99",
    "session_id": "session_001"
  }'`,
    response: `{
  "answer": "Based on architecture_spec.txt [c_001]...",
  "sources": ["architecture_spec.txt"],
  "citations": [
    {
      "document_name": "architecture_spec.txt",
      "chunk_id": "c_001",
      "relevance_score": 0.89,
      "snippet": "Parent-document retrievers split documents..."
    }
  ],
  "retrieved_context": [...],
  "memory": {
    "user_id": "usr_99",
    "memories_applied": ["User works in Python..."],
    "new_facts_extracted": []
  },
  "telemetry": {
    "retrieval_latency_ms": 14.28,
    "rerank_latency_ms": 42.15,
    "generation_latency_ms": 128.40,
    "total_latency_ms": 184.83
  }
}`
  },
  {
    method: 'GET',
    path: '/api/users/{user_id}/memories',
    title: 'Get User Semantic Memories',
    desc: 'Retrieves all persistent semantic facts and preferences extracted for a specific user ID.',
    curl: `curl -X GET http://localhost:8000/api/users/usr_99/memories`,
    response: `{
  "user_id": "usr_99",
  "total_memories": 2,
  "memories": [
    {
      "id": "mem_a1b2c3d4",
      "user_id": "usr_99",
      "fact": "User works primarily in Python.",
      "category": "preference",
      "created_at": "2026-11-20T10:45:00Z"
    }
  ]
}`
  },
  {
    method: 'POST',
    path: '/api/documents/upload',
    title: 'Upload & Ingest Document',
    desc: 'Uploads a PDF, TXT, or DOCX document. Splits it into ~1000 char parent chunks and ~200 char child chunks, indexing embeddings and BM25 tokens.',
    curl: `curl -X POST http://localhost:8000/api/documents/upload \\
  -F "file=@sample_rag_spec.pdf"`,
    response: `{
  "status": "success",
  "message": "Successfully ingested 'sample_rag_spec.pdf' with 4 parent chunks and 18 child chunks.",
  "document": {
    "document_id": "doc_a1b2c3d4e5",
    "filename": "sample_rag_spec.pdf",
    "file_type": "pdf",
    "file_size_bytes": 24510,
    "char_count": 3890,
    "parent_chunk_count": 4,
    "child_chunk_count": 18,
    "created_at": "1732098000.0"
  }
}`
  },
  {
    method: 'GET',
    path: '/api/health',
    title: 'System Health & Readiness',
    desc: 'Returns system operational status, active API key configurations, and vector index statistics.',
    curl: `curl -X GET http://localhost:8000/api/health`,
    response: `{
  "status": "healthy",
  "service": "Advanced RAG Agent with Context Compression & Semantic Memory",
  "version": "1.0.0",
  "mode": "production",
  "configuration": {
    "gemini_api_configured": true,
    "cohere_api_configured": true,
    "mem0_api_configured": true,
    "qdrant_configured": false
  },
  "stats": {
    "total_documents": 3,
    "total_indexed_child_chunks": 42,
    "parent_chunk_size": 1000,
    "child_chunk_size": 200,
    "rrf_k": 60,
    "top_n_rerank": 5
  }
}`
  }
];

export default function ApiDocs() {
  const [copiedIdx, setCopiedIdx] = useState(null);

  const copyToClipboard = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Code2 className="w-6 h-6 text-cyan-400" />
          <span>FastAPI Endpoint Reference</span>
        </h2>
        <p className="text-xs text-slate-400">
          Interactive documentation and cURL examples for all production REST endpoints.
        </p>
      </div>

      <div className="space-y-6">
        {ENDPOINTS.map((ep, idx) => (
          <GlassCard key={idx} className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-3">
              <div className="flex items-center gap-3">
                <span
                  className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold ${
                    ep.method === 'POST'
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                      : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  }`}
                >
                  {ep.method}
                </span>
                <span className="text-sm font-mono text-white font-semibold">{ep.path}</span>
              </div>
              <span className="text-xs text-slate-300 font-medium">{ep.title}</span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">{ep.desc}</p>

            {/* cURL Request */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <Terminal className="w-3.5 h-3.5" /> cURL Example
                </span>
                <button
                  onClick={() => copyToClipboard(ep.curl, idx)}
                  className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors"
                >
                  {copiedIdx === idx ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedIdx === idx ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <pre className="p-3.5 rounded-xl bg-black/40 border border-white/10 text-xs font-mono text-cyan-300 overflow-x-auto">
                {ep.curl}
              </pre>
            </div>

            {/* Expected JSON Response */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-mono text-slate-400 block">Response JSON Schema (200 OK)</span>
              <pre className="p-3.5 rounded-xl bg-black/40 border border-white/10 text-xs font-mono text-slate-300 overflow-x-auto max-h-48">
                {ep.response}
              </pre>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}
