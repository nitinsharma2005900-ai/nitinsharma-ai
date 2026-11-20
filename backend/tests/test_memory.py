import unittest
import tempfile
from pathlib import Path

from app.memory.semantic_memory import SemanticMemoryStore
from app.rag.generator import GeminiGenerator


class TestSemanticMemory(unittest.TestCase):
    """Test suite for Mem0 semantic memory extraction and multi-session persona adaptation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.temp_dir.name) / "test_memories.json"
        self.memory_store = SemanticMemoryStore(storage_path=self.storage_file)
        self.generator = GeminiGenerator()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_06_memory_fact_extraction(self):
        """Test 6: Verify extraction and saving of user facts and preferences."""
        user_id = "usr_99"
        message = "Hello! I work in Python and prefer brief, code-only responses."

        new_facts = self.memory_store.extract_and_store(user_id, message)

        self.assertGreater(len(new_facts), 0)

        # Check stored memories in store
        stored = self.memory_store.get_user_memories(user_id)
        stored_texts = " ".join(m.fact.lower() for m in stored)

        self.assertIn("python", stored_texts)
        self.assertTrue("code-only" in stored_texts or "code only" in stored_texts or "brief" in stored_texts)

        # Persistence check: reload from disk
        reloaded_store = SemanticMemoryStore(storage_path=self.storage_file)
        reloaded_mems = reloaded_store.get_user_memories(user_id)
        self.assertEqual(len(reloaded_mems), len(stored))

    def test_07_multi_session_persona_adaptation(self):
        """Test 7: Verify multi-session persona adaptation (merge sort test case)."""
        user_id = "usr_99"

        # Session 1: User introduces preference
        query_session_1 = "Hello! I work in Python and prefer brief, code-only responses."
        self.memory_store.extract_and_store(user_id, query_session_1)

        # Verify fact exists in memory
        memories = self.memory_store.get_user_memories(user_id)
        self.assertTrue(any("python" in m.fact.lower() for m in memories))

        # Session 2: User requests merge sort in a new session
        query_session_2 = "Write a quick merge sort routine."
        persona_prompt = self.memory_store.build_persona_prompt(user_id)

        # Assert persona prompt contains the directives
        self.assertIn("Python", persona_prompt)
        self.assertTrue("code-only" in persona_prompt or "code" in persona_prompt)

        # Run generator with the adapted persona
        answer, sources, citations = self.generator.generate(
            query=query_session_2,
            documents=[],
            persona_context=persona_prompt,
        )

        # Verify agent bypasses long explanations and returns strictly a Python code block
        self.assertTrue(answer.strip().startswith("```python"), "Answer must begin with ```python code block")
        self.assertTrue(answer.strip().endswith("```"), "Answer must end with ```")
        self.assertIn("def merge_sort", answer)
        # Verify no conversational filler or commentary outside code block
        stripped_answer = answer.strip()
        self.assertNotIn("here is", stripped_answer.lower())
        self.assertNotIn("certainly", stripped_answer.lower())
        self.assertNotIn("sure,", stripped_answer.lower())


if __name__ == "__main__":
    unittest.main()
