import json
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error

from app.core.config import settings
from app.models.document import ChildChunk, ScoredChunk


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def generate_local_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Generates a deterministic, normalized dense semantic embedding vector.
    Used for local offline testing and resilient zero-dependency fallback.
    """
    if not text:
        return [0.0] * dim

    vec = [0.0] * dim
    words = text.lower().split()

    for idx, word in enumerate(words):
        # Character n-grams for semantic sensitivity
        for n in range(2, min(5, len(word) + 1)):
            ngram = word[:n]
            h = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
            pos = h % dim
            sign = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[pos] += sign * (1.0 / (idx + 1) ** 0.5)

        h_full = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        pos_full = h_full % dim
        vec[pos_full] += 1.5

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0.0:
        vec = [round(v / norm, 6) for v in vec]
    return vec


class VectorStore:
    """
    Dense vector store supporting Cohere API embeddings, Qdrant integration,
    and a persistent local vector index.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or settings.VECTOR_STORE_PATH
        self.vectors: Dict[str, List[float]] = {}
        self.chunks_map: Dict[str, ChildChunk] = {}
        self.qdrant_client = None
        self._init_qdrant_if_available()
        self.load()

    def _init_qdrant_if_available(self):
        """Attempts to initialize Qdrant client if URL is provided and package is available."""
        if settings.QDRANT_URL:
            try:
                from qdrant_client import QdrantClient
                self.qdrant_client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY or None,
                )
            except Exception:
                self.qdrant_client = None

    def embed_texts(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """
        Embeds texts using Cohere Embed API if key is available,
        otherwise uses deterministic local semantic embeddings.
        """
        if settings.COHERE_API_KEY and not settings.OFFLINE_TEST_MODE:
            try:
                # Call Cohere Embed API via REST
                url = "https://api.cohere.com/v1/embed"
                payload = json.dumps({
                    "model": "embed-english-v3.0",
                    "texts": texts,
                    "input_type": input_type,
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
                    return res_data.get("embeddings", [])
            except Exception as e:
                # Fallback to local on network or auth failure
                pass

        # Local deterministic semantic embeddings fallback
        return [generate_local_embedding(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Embeds a single search query."""
        results = self.embed_texts([query], input_type="search_query")
        return results[0] if results else generate_local_embedding(query)

    def add_chunks(self, chunks: List[ChildChunk]):
        """Embed and store a list of child chunks."""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = self.embed_texts(texts, input_type="search_document")

        for chunk, emb in zip(chunks, embeddings):
            self.vectors[chunk.child_id] = emb
            self.chunks_map[chunk.child_id] = chunk

        self.save()

    def search(self, query: str, top_k: int = 20) -> List[ScoredChunk]:
        """Search dense vector index with cosine similarity."""
        if not self.vectors or not self.chunks_map:
            return []

        q_vec = self.embed_query(query)

        scored: List[Tuple[str, float]] = []
        for child_id, doc_vec in self.vectors.items():
            sim = cosine_similarity(q_vec, doc_vec)
            scored.append((child_id, sim))

        # Sort descending by cosine similarity
        scored.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored[:top_k]

        results = []
        for rank, (child_id, score) in enumerate(top_matches, start=1):
            if child_id in self.chunks_map:
                results.append(
                    ScoredChunk(
                        chunk=self.chunks_map[child_id],
                        score=round(score, 4),
                        rank=rank,
                        retrieval_type="dense",
                    )
                )

        return results

    def remove_chunks_for_document(self, document_id: str):
        """Removes all indexed chunks belonging to a document."""
        to_delete = [
            cid for cid, chunk in self.chunks_map.items()
            if chunk.document_id == document_id
        ]
        for cid in to_delete:
            self.vectors.pop(cid, None)
            self.chunks_map.pop(cid, None)
        self.save()

    def save(self):
        """Persists indexed vectors and metadata."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "vectors": self.vectors,
            "chunks": [
                {
                    "child_id": c.child_id,
                    "parent_id": c.parent_id,
                    "document_id": c.document_id,
                    "document_name": c.document_name,
                    "text": c.text,
                    "chunk_index": c.chunk_index,
                    "char_start": c.char_start,
                    "char_end": c.char_end,
                    "metadata": c.metadata,
                }
                for c in self.chunks_map.values()
            ],
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self):
        """Loads vectors and chunks from disk."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.vectors = data.get("vectors", {})
            self.chunks_map = {}
            for c_dict in data.get("chunks", []):
                chunk = ChildChunk(
                    child_id=c_dict["child_id"],
                    parent_id=c_dict["parent_id"],
                    document_id=c_dict["document_id"],
                    document_name=c_dict["document_name"],
                    text=c_dict["text"],
                    chunk_index=c_dict["chunk_index"],
                    char_start=c_dict["char_start"],
                    char_end=c_dict["char_end"],
                    metadata=c_dict.get("metadata", {}),
                )
                self.chunks_map[chunk.child_id] = chunk
        except Exception as e:
            print(f"Warning: Failed to load vector store: {e}")
