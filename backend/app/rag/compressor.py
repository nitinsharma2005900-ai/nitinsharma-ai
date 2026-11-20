import json
import urllib.request
import urllib.error
import re
from typing import List, Tuple, Dict, Any, Optional

from app.core.config import settings
from app.models.document import ParentChunk, ChildChunk, RerankedDocument


def local_relevance_score(query: str, text: str) -> float:
    """
    Computes a deterministic semantic relevance score in [0.0, 1.0]
    between query and text for offline testing and fallback execution.
    """
    if not query or not text:
        return 0.0

    q_words = set(re.findall(r"\b\w+\b", query.lower()))
    t_words = set(re.findall(r"\b\w+\b", text.lower()))

    if not q_words or not t_words:
        return 0.0

    overlap = q_words.intersection(t_words)
    jaccard = len(overlap) / len(q_words.union(t_words))
    recall = len(overlap) / len(q_words)

    # Word proximity bonus if multiple query terms appear close together
    phrase_bonus = 0.0
    q_str = " ".join(q_words)
    if q_str in text.lower():
        phrase_bonus = 0.25

    raw_score = 0.5 * recall + 0.3 * jaccard + phrase_bonus
    return min(max(round(raw_score, 4), 0.0), 1.0)


def compress_text(text: str, query: str, max_chars: int = 600) -> str:
    """
    Compress context by extracting the most query-relevant sentences
    from the full parent chunk, eliminating noise and reducing token count.
    """
    if len(text) <= max_chars:
        return text

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) <= 2:
        return text[:max_chars].strip()

    q_terms = set(re.findall(r"\b\w+\b", query.lower()))
    scored_sentences = []

    for idx, s in enumerate(sentences):
        s_terms = set(re.findall(r"\b\w+\b", s.lower()))
        score = len(q_terms.intersection(s_terms))
        # Slight positional bias to preserve document flow
        pos_weight = 1.0 / (idx + 1) ** 0.3
        scored_sentences.append((s, score + pos_weight, idx))

    # Pick top sentences until max_chars is reached
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    selected = []
    total_len = 0

    for s, score, idx in scored_sentences:
        if total_len + len(s) > max_chars and selected:
            break
        selected.append((s, idx))
        total_len += len(s)

    # Restore original reading order
    selected.sort(key=lambda x: x[1])
    compressed = " ".join(s for s, _ in selected)
    return compressed.strip()


class CohereReRankCompressor:
    """
    Reranks candidate parent documents using Cohere ReRank API (or deterministic offline reranker),
    applies score thresholding, filters to top N (default: 5), and performs context compression.
    """

    def __init__(
        self,
        model: str = "rerank-english-v3.0",
        top_n: int = 5,
        threshold: Optional[float] = None,
    ):
        self.model = model or settings.COHERE_RERANK_MODEL
        self.top_n = top_n or settings.TOP_N_RERANK
        self.threshold = (
            settings.RELEVANCE_SCORE_THRESHOLD if threshold is None else threshold
        )

    def rerank_and_compress(
        self,
        query: str,
        candidates: List[Tuple[ParentChunk, ChildChunk, float]],
    ) -> List[RerankedDocument]:
        """
        Takes candidates (parent, child, rrf_score), reranks via Cohere ReRank,
        filters by score threshold, takes top_n, and applies context compression.
        """
        if not candidates:
            return []

        # Prepare document texts for reranker
        doc_texts = [parent.text for parent, _, _ in candidates]

        scores: List[float] = []

        # Attempt live Cohere ReRank if key is provided and not in offline test mode
        if settings.COHERE_API_KEY and not settings.OFFLINE_TEST_MODE:
            try:
                url = "https://api.cohere.com/v1/rerank"
                payload = json.dumps({
                    "model": self.model,
                    "query": query,
                    "documents": doc_texts,
                    "top_n": min(len(doc_texts), 20),
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {settings.COHERE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    # Map Cohere response results back by index
                    cohere_scores = {item["index"]: float(item["relevance_score"]) for item in res_data.get("results", [])}
                    scores = [cohere_scores.get(i, 0.0) for i in range(len(doc_texts))]
            except Exception:
                # Fallback to local scoring if API fails
                scores = []

        # If live API was not used or failed, use local deterministic relevance scoring
        if not scores:
            scores = [local_relevance_score(query, text) for text in doc_texts]

        # Combine candidates with scores
        scored_candidates: List[Tuple[ParentChunk, ChildChunk, float, float]] = []
        for (parent, child, rrf_s), score in zip(candidates, scores):
            scored_candidates.append((parent, child, rrf_s, score))

        # Sort descending by ReRank relevance score
        scored_candidates.sort(key=lambda x: x[3], reverse=True)

        # Apply relevance score thresholding & top_n filtering
        results: List[RerankedDocument] = []
        for parent, child, rrf_s, score in scored_candidates:
            if score < self.threshold:
                continue

            compressed = compress_text(parent.text, query)

            results.append(
                RerankedDocument(
                    parent_chunk=parent,
                    matched_child=child,
                    relevance_score=round(score, 4),
                    compressed_text=compressed,
                    rrf_score=round(rrf_s, 6),
                )
            )

            if len(results) >= self.top_n:
                break

        return results
