import unittest
from app.models.document import ParentChunk, ChildChunk
from app.rag.compressor import CohereReRankCompressor, compress_text


class TestCohereReRank(unittest.TestCase):
    """Test suite for Cohere ReRank top-5 filtering, threshold filtering, and compression."""

    def setUp(self):
        self.compressor = CohereReRankCompressor(
            model="rerank-english-v3.0",
            top_n=5,
            threshold=0.25,
        )

        # Create 8 candidate parent chunks with varying degrees of relevance
        self.candidates = []
        texts = [
            "Cohere ReRank takes candidate documents and computes deep cross-encoder relevance scores.",
            "Reciprocal Rank Fusion merges dense vector search with sparse BM25 lexical ranking.",
            "FastAPI exposes RESTful endpoints with Pydantic request validation and async handlers.",
            "Qdrant is a high-performance vector database with HNSW indexing and payload filtering.",
            "Semantic memory stores user persona facts and preferences across multiple chat sessions.",
            "Cooking pasta requires boiling salted water and testing for al dente texture.",
            "Baking bread involves kneading yeast dough and proofing until double in size.",
            "Astronomy studies celestial objects such as stars, planets, and galaxies in outer space.",
        ]

        for i, txt in enumerate(texts):
            p = ParentChunk(
                parent_id=f"p_{i:03d}",
                document_id=f"doc_{i:03d}",
                document_name=f"file_{i}.txt",
                text=txt,
                chunk_index=i,
            )
            c = ChildChunk(
                child_id=f"c_{i:03d}",
                parent_id=p.parent_id,
                document_id=p.document_id,
                document_name=p.document_name,
                text=txt[:60],
                chunk_index=0,
                char_start=0,
                char_end=60,
            )
            # Tuple: (parent, child, rrf_score)
            self.candidates.append((p, c, 0.03 - (i * 0.002)))

    def test_04_cohere_rerank_top5_filtering(self):
        """Test 4: Verify compressor limits results to top 5 candidates."""
        query = "How does Cohere ReRank compute cross-encoder relevance scores?"
        results = self.compressor.rerank_and_compress(query, self.candidates)

        # Must not exceed top_n (5)
        self.assertLessEqual(len(results), 5)
        self.assertGreater(len(results), 0)

        # Top document should be the one about Cohere ReRank
        self.assertIn("Cohere ReRank", results[0].parent_chunk.text)
        self.assertGreaterEqual(results[0].relevance_score, self.compressor.threshold)

        # Results should be strictly ordered descending by relevance score
        for i in range(len(results) - 1):
            self.assertGreaterEqual(results[i].relevance_score, results[i + 1].relevance_score)

    def test_05_relevance_threshold_filtering(self):
        """Test 5: Verify retriever drops document chunks falling below relevance threshold."""
        query = "Deep learning transformers attention mechanism"

        # Using a high threshold of 0.8
        high_threshold_compressor = CohereReRankCompressor(
            model="rerank-english-v3.0",
            top_n=5,
            threshold=0.85,
        )
        results_high = high_threshold_compressor.rerank_and_compress(query, self.candidates)

        # Completely unrelated texts (cooking, baking, stars) should not pass high threshold
        for doc in results_high:
            self.assertGreaterEqual(doc.relevance_score, 0.85)

        # Using standard threshold
        results_standard = self.compressor.rerank_and_compress(query, self.candidates)
        for doc in results_standard:
            self.assertGreaterEqual(
                doc.relevance_score,
                self.compressor.threshold,
                f"Document {doc.parent_chunk.parent_id} score {doc.relevance_score} is below threshold {self.compressor.threshold}"
            )

    def test_context_compression_logic(self):
        """Verify context compression reduces token footprint."""
        long_text = (
            "Introduction to database engines. Many storage engines exist today. "
            "Qdrant specializes in dense vector similarity search using HNSW graphs. "
            "It provides sub-millisecond nearest neighbor search over millions of vectors. "
            "In conclusion, vectors allow semantic search across unstructured data."
        )
        compressed = compress_text(long_text, query="Qdrant dense vector similarity search", max_chars=120)
        self.assertLessEqual(len(compressed), 120)
        self.assertIn("Qdrant", compressed)


if __name__ == "__main__":
    unittest.main()
