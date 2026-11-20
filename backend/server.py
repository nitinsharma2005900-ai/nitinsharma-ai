import json
import os
import sys
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings, UPLOAD_DIR, STORAGE_DIR, BASE_DIR
from app.rag.pipeline import rag_pipeline
from app.schemas.chat import ChatRequest
from app.schemas.memory import ClearMemoryRequest


class RAGRequestHandler(SimpleHTTPRequestHandler):
    """
    Unified HTTP Server handling both RAG REST API endpoints and Web UI.
    """

    def end_headers(self):
        # Enable CORS
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Health check: /api/health
        if path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            docs_count = len(rag_pipeline.doc_service.list_documents())
            children_count = len(rag_pipeline.doc_service.get_all_child_chunks())
            payload = {
                "status": "healthy",
                "service": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "mode": "offline_test" if settings.OFFLINE_TEST_MODE else "production",
                "configuration": {
                    "gemini_api_configured": bool(settings.GEMINI_API_KEY),
                    "cohere_api_configured": bool(settings.COHERE_API_KEY),
                    "mem0_api_configured": bool(settings.MEM0_API_KEY),
                    "qdrant_configured": bool(settings.QDRANT_URL),
                },
                "stats": {
                    "total_documents": docs_count,
                    "total_indexed_child_chunks": children_count,
                    "parent_chunk_size": settings.PARENT_CHUNK_SIZE,
                    "child_chunk_size": settings.CHILD_CHUNK_SIZE,
                    "rrf_k": settings.RRF_K,
                    "top_n_rerank": settings.TOP_N_RERANK,
                },
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
            return

        # 2. Document list: /api/documents
        if path == "/api/documents":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            docs = rag_pipeline.doc_service.list_documents()
            items = []
            for doc in docs:
                total_children = sum(len(p.child_ids) for p in doc.parent_chunks)
                items.append({
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "file_size_bytes": doc.file_size_bytes,
                    "char_count": doc.char_count,
                    "parent_chunk_count": len(doc.parent_chunks),
                    "child_chunk_count": total_children,
                    "created_at": str(doc.created_at),
                })
            res = {"total": len(items), "documents": items}
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            return

        # 3. User memories: /api/users/{user_id}/memories
        if path.startswith("/api/users/") and path.endswith("/memories"):
            parts = path.strip("/").split("/")
            if len(parts) == 4:
                user_id = parts[2]
                mems = rag_pipeline.memory_store.get_user_memories(user_id)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                res = {
                    "user_id": user_id,
                    "total_memories": len(mems),
                    "memories": [
                        {
                            "id": m.id,
                            "user_id": m.user_id,
                            "fact": m.fact,
                            "category": m.category,
                            "created_at": m.created_at,
                        }
                        for m in mems
                    ],
                }
                self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
                return

        # 4. Web UI: serve built frontend or embedded glassmorphism SPA
        static_html_path = backend_dir / "static" / "index.html"
        if static_html_path.exists() and (path == "/" or not path.startswith("/api")):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(static_html_path.read_bytes())
            return

        # Default fallback for unhandled GET
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "endpoints": ["/api/health", "/api/chat", "/api/documents", "/api/users/usr_99/memories", "/api/analytics/inspect"],
        }).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # 1. Chat endpoint: /api/chat
        if path == "/api/chat":
            data = json.loads(body.decode("utf-8"))
            query = data.get("query", "")
            user_id = data.get("user_id", "usr_99")
            session_id = data.get("session_id", "session_001")

            response = rag_pipeline.execute_chat(query=query, user_id=user_id, session_id=session_id)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            res_payload = {
                "answer": response.answer,
                "sources": response.sources,
                "citations": [
                    {
                        "document_name": c.document_name,
                        "chunk_id": c.chunk_id,
                        "relevance_score": c.relevance_score,
                        "snippet": c.snippet,
                    }
                    for c in response.citations
                ],
                "retrieved_context": [
                    {
                        "child_id": ctx.child_id,
                        "parent_id": ctx.parent_id,
                        "document_id": ctx.document_id,
                        "document_name": ctx.document_name,
                        "text": ctx.text,
                        "rerank_score": ctx.rerank_score,
                        "rrf_score": ctx.rrf_score,
                    }
                    for ctx in response.retrieved_context
                ],
                "memory": {
                    "user_id": response.memory.user_id,
                    "memories_applied": response.memory.memories_applied,
                    "new_facts_extracted": response.memory.new_facts_extracted,
                },
                "telemetry": {
                    "retrieval_latency_ms": response.telemetry.retrieval_latency_ms,
                    "rerank_latency_ms": response.telemetry.rerank_latency_ms,
                    "generation_latency_ms": response.telemetry.generation_latency_ms,
                    "total_latency_ms": response.telemetry.total_latency_ms,
                },
            }
            self.wfile.write(json.dumps(res_payload, indent=2).encode("utf-8"))
            return

        # 2. Clear memory: /api/memory/clear
        if path == "/api/memory/clear":
            data = json.loads(body.decode("utf-8"))
            user_id = data.get("user_id", "usr_99")
            cleared = rag_pipeline.memory_store.clear_user_memories(user_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = {"status": "success", "message": f"Cleared {cleared} memories", "cleared_count": cleared, "user_id": user_id}
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            return

        # 3. Analytics inspection: /api/analytics/inspect
        if path == "/api/analytics/inspect":
            data = json.loads(body.decode("utf-8"))
            query = data.get("query", "")
            user_id = data.get("user_id", "usr_99")

            from app.retrieval.hybrid import HybridRetriever
            from app.core.telemetry import TelemetryTimer

            timer = TelemetryTimer()
            hybrid = HybridRetriever(
                vector_store=rag_pipeline.vector_store,
                bm25_retriever=rag_pipeline.bm25_retriever,
                k=settings.RRF_K,
            )
            with timer.measure("retrieval"):
                fused_candidates, analytics = hybrid.retrieve(query, top_k_candidates=20)
                parent_candidates = rag_pipeline.parent_retriever.retrieve_parents(fused_candidates, max_parents=20)

            with timer.measure("rerank"):
                reranked_docs = rag_pipeline.compressor.rerank_and_compress(query, parent_candidates)

            timings = timer.finish()

            res = {
                "query": query,
                "dense_results": analytics.get("dense_top", []),
                "sparse_results": analytics.get("sparse_top", []),
                "rrf_fused": [
                    {
                        "child_id": f.child_chunk.child_id,
                        "rrf_score": f.rrf_score,
                        "dense_rank": f.dense_rank,
                        "sparse_rank": f.sparse_rank,
                        "text": f.child_chunk.text[:120],
                        "doc_name": f.child_chunk.document_name,
                    }
                    for f in fused_candidates[:10]
                ],
                "reranked_top5": [
                    {
                        "parent_id": d.parent_chunk.parent_id,
                        "doc_name": d.parent_chunk.document_name,
                        "relevance_score": d.relevance_score,
                        "rrf_score": d.rrf_score,
                        "original_len": len(d.parent_chunk.text),
                        "compressed_len": len(d.compressed_text),
                        "compressed_text": d.compressed_text,
                    }
                    for d in reranked_docs
                ],
                "telemetry": timings,
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            return

        # 4. Document upload: /api/documents/upload
        if path == "/api/documents/upload":
            content_type = self.headers.get("Content-Type", "")
            filename = f"document_{int(time.time())}.txt"
            file_bytes = b""

            if "multipart/form-data" in content_type:
                import re
                # Extract boundary
                boundary_match = re.search(r"boundary=([^\s;]+)", content_type)
                if boundary_match:
                    boundary = boundary_match.group(1).strip().encode("utf-8")
                    parts = body.split(b"--" + boundary)
                    for part in parts:
                        if b'filename="' in part:
                            header_end = part.find(b"\r\n\r\n")
                            if header_end != -1:
                                headers_part = part[:header_end].decode("utf-8", errors="ignore")
                                fn_match = re.search(r'filename="([^"]+)"', headers_part)
                                if fn_match:
                                    filename = fn_match.group(1)
                                part_body = part[header_end + 4 :]
                                if part_body.endswith(b"\r\n"):
                                    part_body = part_body[:-2]
                                file_bytes = part_body
                                break
            else:
                file_bytes = body

            if not file_bytes:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No file content received."}).encode("utf-8"))
                return

            # Clean and sanitize filename
            safe_filename = Path(filename).name
            save_path = settings.UPLOAD_DIR / f"upload_{safe_filename}"
            save_path.write_bytes(file_bytes)

            try:
                record = rag_pipeline.ingest_document(save_path, filename=safe_filename)
                total_children = sum(len(p.child_ids) for p in record.parent_chunks)
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                res = {
                    "status": "success",
                    "message": f"Successfully ingested '{safe_filename}' with {len(record.parent_chunks)} parent chunks and {total_children} child chunks.",
                    "document": {
                        "document_id": record.document_id,
                        "filename": record.filename,
                        "file_type": record.file_type,
                        "file_size_bytes": record.file_size_bytes,
                        "char_count": record.char_count,
                        "parent_chunk_count": len(record.parent_chunks),
                        "child_chunk_count": total_children,
                        "created_at": str(record.created_at),
                    }
                }
                self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to ingest file: {str(e)}"}).encode("utf-8"))
            finally:
                if save_path.exists():
                    try:
                        save_path.unlink()
                    except Exception:
                        pass
            return

        # 5. Set API keys: /api/config/keys
        if path == "/api/config/keys":
            data = json.loads(body.decode("utf-8"))
            gemini_key = data.get("gemini_api_key", "").strip()
            cohere_key = data.get("cohere_api_key", "").strip()
            
            # Update current process environment
            if gemini_key:
                os.environ["GEMINI_API_KEY"] = gemini_key
            if cohere_key:
                os.environ["COHERE_API_KEY"] = cohere_key

            # Persist to .env files
            env_paths = [settings.BASE_DIR / ".env", settings.BASE_DIR.parent / ".env"]
            for env_path in env_paths:
                env_content = ""
                if env_path.exists():
                    env_content = env_path.read_text(encoding="utf-8")
                
                if gemini_key:
                    if "GEMINI_API_KEY=" in env_content:
                        env_content = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={gemini_key}", env_content)
                    else:
                        env_content += f"\nGEMINI_API_KEY={gemini_key}\n"
                
                if cohere_key:
                    if "COHERE_API_KEY=" in env_content:
                        env_content = re.sub(r"COHERE_API_KEY=.*", f"COHERE_API_KEY={cohere_key}", env_content)
                    else:
                        env_content += f"\nCOHERE_API_KEY={cohere_key}\n"
                
                env_path.write_text(env_content.strip() + "\n", encoding="utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = {
                "status": "success",
                "message": "API keys updated and persisted to .env successfully.",
                "gemini_configured": bool(os.environ.get("GEMINI_API_KEY")),
                "cohere_configured": bool(os.environ.get("COHERE_API_KEY")),
            }
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/documents/"):
            doc_id = path.split("/")[-1]
            success = rag_pipeline.delete_document(doc_id)
            if success:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "document_id": doc_id}).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
            return

        if path.startswith("/api/users/") and "/memories/" in path:
            parts = path.strip("/").split("/")
            if len(parts) == 5:
                user_id = parts[2]
                memory_id = parts[4]
                success = rag_pipeline.memory_store.delete_memory(user_id, memory_id)
                self.send_response(200 if success else 404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success" if success else "not_found"}).encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()


def run_server(host="0.0.0.0", port=8000):
    print(f"Starting Advanced RAG Agent server on http://{host}:{port} ...")
    server = ThreadingHTTPServer((host, port), RAGRequestHandler)
    print(f"Server live at http://127.0.0.1:{port}/api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port=port)
