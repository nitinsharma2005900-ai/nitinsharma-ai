import math
import re
from typing import List, Dict, Set, Tuple
from collections import Counter

from app.models.document import ChildChunk, ScoredChunk


# Common English stopwords
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me",
    "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens, filtering stopwords."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


class BM25Retriever:
    """
    Okapi BM25 implementation for sparse lexical retrieval on child chunks.
    Parameters:
      k1: Term frequency saturation parameter (default: 1.5)
      b: Document length normalization parameter (default: 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: Dict[str, int] = {}
        self.term_freqs: Dict[str, Counter] = {}
        self.doc_freqs: Counter = Counter()
        self.idf: Dict[str, float] = {}
        self.chunks_map: Dict[str, ChildChunk] = {}

    def fit(self, chunks: List[ChildChunk]):
        """Index a collection of child chunks."""
        self.corpus_size = len(chunks)
        self.chunks_map = {c.child_id: c for c in chunks}
        self.doc_lengths = {}
        self.term_freqs = {}
        self.doc_freqs = Counter()
        self.idf = {}

        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        total_length = 0
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            doc_len = len(tokens)
            self.doc_lengths[chunk.child_id] = doc_len
            total_length += doc_len

            counts = Counter(tokens)
            self.term_freqs[chunk.child_id] = counts

            # Update document frequencies (unique terms per document)
            for term in counts.keys():
                self.doc_freqs[term] += 1

        self.avg_doc_len = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Precompute IDF with standard Robertson-Spärck Jones formula
        for term, df in self.doc_freqs.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 20) -> List[ScoredChunk]:
        """Search the indexed chunks using BM25 scoring."""
        if not self.chunks_map or self.corpus_size == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: Dict[str, float] = {}

        for q_term in query_tokens:
            if q_term not in self.idf:
                continue

            idf_val = self.idf[q_term]

            for chunk_id, tf_counter in self.term_freqs.items():
                tf = tf_counter.get(q_term, 0)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths.get(chunk_id, 1)
                norm = 1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0))
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * norm
                bm25_term_score = idf_val * (numerator / denominator)

                scores[chunk_id] = scores.get(chunk_id, 0.0) + bm25_term_score

        # Sort by score descending
        sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]

        results = []
        for rank, (chunk_id, score) in enumerate(sorted_items, start=1):
            results.append(
                ScoredChunk(
                    chunk=self.chunks_map[chunk_id],
                    score=round(score, 4),
                    rank=rank,
                    retrieval_type="sparse",
                )
            )

        return results
