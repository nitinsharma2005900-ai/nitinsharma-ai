import unittest
from app.models.document import ChildChunk, ScoredChunk
from app.retrieval.hybrid import HybridRetriever, compute_rrf_score
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore


class TestRRFFusion(unittest.TestCase):
    """Test suite for Reciprocal Rank Fusion (RRF) and Dense-Sparse Merging."""

    def setUp(self):
        self.chunk_a = ChildChunk(
            child_id="c_001",
            parent_id="p_001",
            document_id="doc_01",
            document_name="doc_a.txt",
            text="Quantum computing utilizes qubits for superposition.",
            chunk_index=0,
            char_start=0,
            char_end=50,
        )
        self.chunk_b = ChildChunk(
            child_id="c_002",
            parent_id="p_002",
            document_id="doc_02",
            document_name="doc_b.txt",
            text="Classical computing relies on deterministic binary bits.",
            chunk_index=0,
            char_start=0,
            char_end=50,
        )
        self.chunk_c = ChildChunk(
            child_id="c_003",
            parent_id="p_003",
            document_id="doc_03",
            document_name="doc_c.txt",
            text="Machine learning models learn patterns from training data.",
            chunk_index=0,
            char_start=0,
            char_end=50,
        )

    def test_01_rrf_fusion_correctness(self):
        """Test 1: Verify RRF score computation formula 1 / (k + rank)."""
        k = 60
        # Rank 1 score
        expected_rank1 = 1.0 / (60 + 1)
        self.assertAlmostEqual(compute_rrf_score(1, k=k), expected_rank1, places=6)

        # Rank 2 score
        expected_rank2 = 1.0 / (60 + 2)
        self.assertAlmostEqual(compute_rrf_score(2, k=k), expected_rank2, places=6)

        # Monotonicity: higher rank (lower number) yields higher score
        self.assertGreater(compute_rrf_score(1, k=k), compute_rrf_score(2, k=k))
        self.assertGreater(compute_rrf_score(5, k=k), compute_rrf_score(20, k=k))

    def test_02_dense_and_sparse_result_merging(self):
        """Test 2: Verify merging of dense and sparse rankings and deduplication."""
        # Create mock vector store and BM25 retriever
        vector_store = VectorStore()
        bm25_retriever = BM25Retriever()

        # Mock search methods
        # Dense ranking: chunk_a (rank 1), chunk_b (rank 2)
        vector_store.search = lambda q, top_k=20: [
            ScoredChunk(chunk=self.chunk_a, score=0.95, rank=1, retrieval_type="dense"),
            ScoredChunk(chunk=self.chunk_b, score=0.80, rank=2, retrieval_type="dense"),
        ]

        # Sparse ranking: chunk_b (rank 1), chunk_c (rank 2)
        bm25_retriever.search = lambda q, top_k=20: [
            ScoredChunk(chunk=self.chunk_b, score=4.5, rank=1, retrieval_type="sparse"),
            ScoredChunk(chunk=self.chunk_c, score=2.1, rank=2, retrieval_type="sparse"),
        ]

        hybrid = HybridRetriever(vector_store=vector_store, bm25_retriever=bm25_retriever, k=60)
        fused, analytics = hybrid.retrieve("computing bits", top_k_candidates=10)

        # Deduplication check: 3 distinct chunks total
        self.assertEqual(len(fused), 3)

        # chunk_b appeared in both (dense rank 2, sparse rank 1)
        # score = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 ~= 0.016129 + 0.016393 ~= 0.032522
        expected_b_score = (1.0 / 62) + (1.0 / 61)

        # chunk_a appeared only in dense (dense rank 1)
        # score = 1/(60+1) = 1/61 ~= 0.016393
        expected_a_score = 1.0 / 61

        # chunk_c appeared only in sparse (sparse rank 2)
        # score = 1/(60+2) = 1/62 ~= 0.016129
        expected_c_score = 1.0 / 62

        # chunk_b should be ranked #1
        self.assertEqual(fused[0].child_chunk.child_id, "c_002")
        self.assertAlmostEqual(fused[0].rrf_score, expected_b_score, places=5)
        self.assertEqual(fused[0].dense_rank, 2)
        self.assertEqual(fused[0].sparse_rank, 1)

        # chunk_a should be ranked #2
        self.assertEqual(fused[1].child_chunk.child_id, "c_001")
        self.assertAlmostEqual(fused[1].rrf_score, expected_a_score, places=5)

        # chunk_c should be ranked #3
        self.assertEqual(fused[2].child_chunk.child_id, "c_003")
        self.assertAlmostEqual(fused[2].rrf_score, expected_c_score, places=5)

        # Verify analytics metadata
        self.assertEqual(analytics["dense_count"], 2)
        self.assertEqual(analytics["sparse_count"], 2)
        self.assertEqual(analytics["fused_count"], 3)


if __name__ == "__main__":
    unittest.main()
