import unittest
import asyncio
from app.schemas.chat import ChatRequest
from app.rag.pipeline import rag_pipeline
from app.api.chat import chat_endpoint
from app.api.memory import get_user_memories, clear_memory
from app.schemas.memory import ClearMemoryRequest


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for FastAPI endpoints and execution latency telemetry."""

    def setUp(self):
        # Clear test memories for clean state
        rag_pipeline.memory_store.clear_user_memories("usr_99")

    def test_08_fastapi_chat_endpoint(self):
        """Test 8: Verify POST /api/chat endpoint response structure."""
        req = ChatRequest(
            query="Hello! I work in Python and prefer brief, code-only responses.",
            user_id="usr_99",
            session_id="session_001",
        )

        response = chat_endpoint(req)

        # Check response fields
        self.assertIsNotNone(response.answer)
        self.assertIsInstance(response.sources, list)
        self.assertIsInstance(response.citations, list)
        self.assertIsInstance(response.retrieved_context, list)
        self.assertEqual(response.memory.user_id, "usr_99")
        self.assertIsInstance(response.memory.new_facts_extracted, list)

    def test_09_memory_retrieval_endpoint(self):
        """Test 9: Verify GET /api/users/{user_id}/memories endpoint."""
        # Add fact first
        rag_pipeline.memory_store.add_memory("usr_99", "User works primarily in Python.")

        res = get_user_memories("usr_99")

        self.assertEqual(res.user_id, "usr_99")
        self.assertGreaterEqual(res.total_memories, 1)
        self.assertTrue(any("python" in m.fact.lower() for m in res.memories))

        # Test clear endpoint
        clear_res = clear_memory(ClearMemoryRequest(user_id="usr_99"))
        self.assertEqual(clear_res.status, "success")
        self.assertGreaterEqual(clear_res.cleared_count, 1)

    def test_10_telemetry_fields_and_numeric_latency_values(self):
        """Test 10: Verify telemetry fields contain valid positive numeric values."""
        req = ChatRequest(
            query="Explain the architecture of parent document retrievers.",
            user_id="usr_99",
            session_id="session_002",
        )

        response = chat_endpoint(req)
        telemetry = response.telemetry

        # Assert all required fields exist
        self.assertTrue(hasattr(telemetry, "retrieval_latency_ms"))
        self.assertTrue(hasattr(telemetry, "rerank_latency_ms"))
        self.assertTrue(hasattr(telemetry, "generation_latency_ms"))
        self.assertTrue(hasattr(telemetry, "total_latency_ms"))

        # Assert all fields contain valid positive numeric values (not None, not 0, not fake strings)
        self.assertIsInstance(telemetry.retrieval_latency_ms, float)
        self.assertIsInstance(telemetry.rerank_latency_ms, float)
        self.assertIsInstance(telemetry.generation_latency_ms, float)
        self.assertIsInstance(telemetry.total_latency_ms, float)

        self.assertGreater(telemetry.retrieval_latency_ms, 0.0)
        self.assertGreater(telemetry.rerank_latency_ms, 0.0)
        self.assertGreater(telemetry.generation_latency_ms, 0.0)
        self.assertGreater(telemetry.total_latency_ms, 0.0)

        # Total latency should be greater than or equal to any individual stage
        self.assertGreaterEqual(telemetry.total_latency_ms, telemetry.retrieval_latency_ms)
        self.assertGreaterEqual(telemetry.total_latency_ms, telemetry.rerank_latency_ms)
        self.assertGreaterEqual(telemetry.total_latency_ms, telemetry.generation_latency_ms)


if __name__ == "__main__":
    unittest.main()
