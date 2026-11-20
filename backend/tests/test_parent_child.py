import unittest
import tempfile
from pathlib import Path

from app.models.document import ChildChunk, FusionResult
from app.services.document_service import DocumentService
from app.retrieval.parent_retriever import ParentDocumentRetriever


class TestParentChildMapping(unittest.TestCase):
    """Test suite for Parent-Child Document Mapping & Retrieval."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.temp_dir.name) / "test_docstore.json"
        self.doc_service = DocumentService(storage_path=self.storage_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_03_parent_child_mapping_and_retrieval(self):
        """Test 3: Verify parent-child chunk segmentation and parent retrieval mapping."""
        # Create a document text > 1500 chars to produce multiple parent and child chunks
        sample_paragraphs = [
            f"Section {i}: Advanced retrieval architectures combine dense semantic vectors with sparse lexical BM25 indexing. "
            f"Parent-document retrievers split documents into small child chunks for granular matching, while mapping each child "
            f"back to a larger parent chunk containing complete semantic context. This eliminates chunk boundary truncation."
            for i in range(1, 8)
        ]
        sample_text = "\n\n".join(sample_paragraphs)

        test_file = Path(self.temp_dir.name) / "sample_rag_spec.txt"
        test_file.write_text(sample_text, encoding="utf-8")

        # Ingest document
        record, child_chunks = self.doc_service.process_and_ingest(test_file, filename="sample_rag_spec.txt")

        # Assert document record created
        self.assertEqual(record.filename, "sample_rag_spec.txt")
        self.assertGreater(len(record.parent_chunks), 1)
        self.assertGreater(len(child_chunks), len(record.parent_chunks))

        # Assert each child chunk points to an existing parent chunk
        for child in child_chunks:
            parent = self.doc_service.get_parent_chunk(child.parent_id)
            self.assertIsNotNone(parent, f"Child {child.child_id} has invalid parent_id {child.parent_id}")
            self.assertIn(child.child_id, parent.child_ids)
            # Child text should be contained within parent text
            self.assertIn(child.text[:40], parent.text)

        # Assert parent chunk sizes are ~1000 chars, child chunk sizes are ~200 chars
        for parent in record.parent_chunks:
            self.assertLessEqual(len(parent.text), 1200)
            self.assertGreaterEqual(len(parent.text), 100)

        for child in child_chunks:
            self.assertLessEqual(len(child.text), 300)

        # Test ParentDocumentRetriever with child chunk matches
        parent_retriever = ParentDocumentRetriever(self.doc_service)
        
        # Pick 3 child chunks from the same parent and 1 from a second parent
        first_parent = record.parent_chunks[0]
        second_parent = record.parent_chunks[1]

        c1 = self.doc_service.get_child_chunk(first_parent.child_ids[0])
        c2 = self.doc_service.get_child_chunk(first_parent.child_ids[1])
        c3 = self.doc_service.get_child_chunk(second_parent.child_ids[0])

        fused_items = [
            FusionResult(child_chunk=c1, rrf_score=0.032),
            FusionResult(child_chunk=c2, rrf_score=0.028),
            FusionResult(child_chunk=c3, rrf_score=0.025),
        ]

        retrieved_parents = parent_retriever.retrieve_parents(fused_items, max_parents=10)

        # Deduplication check: even though 2 child chunks belonged to first_parent,
        # it should only appear once in parent candidates
        self.assertEqual(len(retrieved_parents), 2)

        # Order check: first_parent has higher RRF score (0.032) than second_parent (0.025)
        self.assertEqual(retrieved_parents[0][0].parent_id, first_parent.parent_id)
        self.assertEqual(retrieved_parents[1][0].parent_id, second_parent.parent_id)

        # Context check: retrieved parent contains the complete ~1000 char parent context
        self.assertEqual(retrieved_parents[0][0].text, first_parent.text)


if __name__ == "__main__":
    unittest.main()
