from app.core.compat import APIRouter, status, BaseModel, Field
from typing import Dict, Any, List

from app.core.config import settings
from app.rag.pipeline import rag_pipeline
from app.retrieval.hybrid import HybridRetriever
from app.core.telemetry import TelemetryTimer

router = APIRouter()


class AnalyticsInspectRequest(BaseModel):
    query: str = Field(..., min_length=1)
    user_id: str = "usr_99"


@router.post(
    "/analytics/inspect",
    status_code=status.HTTP_200_OK,
    summary="Inspect RAG retrieval pipeline stages in detail",
)
async def inspect_retrieval(payload: AnalyticsInspectRequest):
    timer = TelemetryTimer()

    # 1. Hybrid retrieval
    hybrid = HybridRetriever(
        vector_store=rag_pipeline.vector_store,
        bm25_retriever=rag_pipeline.bm25_retriever,
        k=settings.RRF_K,
    )

    with timer.measure("retrieval"):
        fused_candidates, analytics = hybrid.retrieve(payload.query, top_k_candidates=20)
        parent_candidates = rag_pipeline.parent_retriever.retrieve_parents(fused_candidates, max_parents=20)

    # 2. ReRanking & context compression
    with timer.measure("rerank"):
        reranked_docs = rag_pipeline.compressor.rerank_and_compress(payload.query, parent_candidates)

    timings = timer.finish()

    return {
        "query": payload.query,
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
