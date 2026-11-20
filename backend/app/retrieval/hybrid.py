from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

from app.core.config import settings
from app.models.document import ChildChunk, ScoredChunk, FusionResult
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore


def compute_rrf_score(rank: int, k: int = 60) -> float:
    """Computes the reciprocal rank score: 1 / (k + rank)."""
    return 1.0 / (k + rank)


class HybridRetriever:
    """
    Hybrid retriever combining dense semantic search and BM25 sparse lexical search
    via Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever,
        k: int = 60,
    ):
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.k = k or settings.RRF_K

    def retrieve(
        self,
        query: str,
        top_k_candidates: int = 20,
    ) -> Tuple[List[FusionResult], Dict[str, Any]]:
        """
        Executes dense and sparse searches, applies RRF, deduplicates,
        and returns fused results alongside breakdown analytics.
        """
        # 1. Retrieve candidates from both indices
        dense_results: List[ScoredChunk] = self.vector_store.search(query, top_k=top_k_candidates)
        sparse_results: List[ScoredChunk] = self.bm25_retriever.search(query, top_k=top_k_candidates)

        # 2. Track ranks and chunks
        chunk_map: Dict[str, ChildChunk] = {}
        rrf_scores: Dict[str, float] = defaultdict(float)
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}
        sparse_scores: Dict[str, float] = {}

        for item in dense_results:
            cid = item.chunk.child_id
            chunk_map[cid] = item.chunk
            dense_ranks[cid] = item.rank
            dense_scores[cid] = item.score
            rrf_scores[cid] += compute_rrf_score(item.rank, self.k)

        for item in sparse_results:
            cid = item.chunk.child_id
            chunk_map[cid] = item.chunk
            sparse_ranks[cid] = item.rank
            sparse_scores[cid] = item.score
            rrf_scores[cid] += compute_rrf_score(item.rank, self.k)

        # 3. Sort by fused RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused_results: List[FusionResult] = []
        for cid in sorted_cids:
            fused_results.append(
                FusionResult(
                    child_chunk=chunk_map[cid],
                    rrf_score=round(rrf_scores[cid], 6),
                    dense_rank=dense_ranks.get(cid),
                    sparse_rank=sparse_ranks.get(cid),
                    dense_score=dense_scores.get(cid),
                    sparse_score=sparse_scores.get(cid),
                )
            )

        analytics = {
            "dense_count": len(dense_results),
            "sparse_count": len(sparse_results),
            "fused_count": len(fused_results),
            "dense_top": [
                {
                    "child_id": d.chunk.child_id,
                    "rank": d.rank,
                    "score": d.score,
                    "text": d.chunk.text[:120],
                    "doc_name": d.chunk.document_name,
                }
                for d in dense_results[:5]
            ],
            "sparse_top": [
                {
                    "child_id": s.chunk.child_id,
                    "rank": s.rank,
                    "score": s.score,
                    "text": s.chunk.text[:120],
                    "doc_name": s.chunk.document_name,
                }
                for s in sparse_results[:5]
            ],
        }

        return fused_results, analytics
