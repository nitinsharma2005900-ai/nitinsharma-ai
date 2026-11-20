import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle,
  AlertCircle,
  File,
  Layers,
  Clock,
  HardDrive,
  Eye,
} from 'lucide-react';
import GlassCard from '../components/GlassCard';
import { api } from '../services/api';

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchDocs = async () => {
    try {
      const res = await api.getDocuments();
      setDocuments(res.documents || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setMessage(null);

    try {
      const res = await api.uploadDocument(file);
      setMessage({ type: 'success', text: res.message });
      fetchDocs();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!confirm(`Are you sure you want to delete '${filename}' and its indexed chunks?`)) return;

    try {
      await api.deleteDocument(docId);
      setMessage({ type: 'success', text: `Deleted '${filename}' from vector and document store.` });
      fetchDocs();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Document Ingestion & Chunk Store</h2>
        <p className="text-xs text-slate-400">
          Upload PDF, TXT, or DOCX files. Documents are automatically partitioned into ~1000 char parent chunks and ~200 char child chunks.
        </p>
      </div>

      {/* Alert Banner */}
      {message && (
        <div
          className={`p-4 rounded-xl flex items-center gap-3 text-xs ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
              : 'bg-rose-500/10 border border-rose-500/20 text-rose-300'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Upload Zone */}
      <GlassCard className="p-8 border-2 border-dashed border-white/10 hover:border-cyan-500/40 text-center transition-colors">
        <input
          type="file"
          id="fileInput"
          accept=".pdf,.txt,.docx,.md"
          onChange={handleFileUpload}
          disabled={isUploading}
          className="hidden"
        />
        <label
          htmlFor="fileInput"
          className="cursor-pointer flex flex-col items-center justify-center space-y-3"
        >
          <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/10">
            <UploadCloud className="w-7 h-7" />
          </div>
          <div>
            <span className="text-sm font-semibold text-white">Click to upload document</span>
            <span className="text-xs text-slate-400 block">Supported: PDF, TXT, DOCX, Markdown (Up to 25MB)</span>
          </div>
          {isUploading && (
            <div className="text-xs text-cyan-400 font-mono animate-pulse">
              Parsing file, creating parent-child chunks & indexing embeddings...
            </div>
          )}
        </label>
      </GlassCard>

      {/* Documents List */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Indexed Documents ({documents.length})</h3>
          </div>
        </div>

        {documents.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            No documents indexed yet. Upload a PDF or TXT to begin hybrid retrieval!
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-cyan-400 flex-shrink-0">
                    <File className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="text-sm font-semibold text-white flex items-center gap-2">
                      <span>{doc.filename}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        {doc.file_type}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono">
                      <span>ID: {doc.document_id}</span>
                      <span>•</span>
                      <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                      <span>•</span>
                      <span>{doc.char_count} chars</span>
                    </div>
                  </div>
                </div>

                {/* Chunks info & Delete */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <div className="px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300">
                      <span className="font-bold">{doc.parent_chunk_count}</span> Parents (~1k)
                    </div>
                    <div className="px-3 py-1 rounded-lg bg-pink-500/10 border border-pink-500/20 text-pink-300">
                      <span className="font-bold">{doc.child_chunk_count}</span> Children (~200)
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(doc.document_id, doc.filename)}
                    className="p-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
