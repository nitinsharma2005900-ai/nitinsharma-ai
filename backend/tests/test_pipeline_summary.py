import unittest
from unittest.mock import Mock

from app.models.document import ChildChunk, DocumentRecord, ParentChunk
from app.rag.pipeline import RAGPipeline


class TestDocumentSummaryContext(unittest.TestCase):
    def setUp(self):
        first_parent = ParentChunk(
            parent_id="parent-1",
            document_id="doc-1",
            document_name="Project_Documentation.pdf",
            text="First complete document section.",
            chunk_index=0,
            child_ids=["child-1"],
        )
        second_parent = ParentChunk(
            parent_id="parent-2",
            document_id="doc-1",
            document_name="Project_Documentation.pdf",
            text="Second complete document section.",
            chunk_index=1,
            child_ids=["child-2"],
        )
        self.document = DocumentRecord(
            document_id="doc-1",
            filename="Project_Documentation.pdf",
            file_type="pdf",
            file_size_bytes=100,
            char_count=200,
            parent_chunks=[first_parent, second_parent],
        )
        self.children = {
            "child-1": ChildChunk(
                child_id="child-1",
                parent_id="parent-1",
                document_id="doc-1",
                document_name="Project_Documentation.pdf",
                text="First child section.",
                chunk_index=0,
                char_start=0,
                char_end=20,
            ),
            "child-2": ChildChunk(
                child_id="child-2",
                parent_id="parent-2",
                document_id="doc-1",
                document_name="Project_Documentation.pdf",
                text="Second child section.",
                chunk_index=0,
                char_start=100,
                char_end=121,
            ),
        }
        self.pipeline = RAGPipeline.__new__(RAGPipeline)
        self.pipeline.doc_service = Mock()
        self.pipeline.doc_service.get_child_chunk.side_effect = self.children.get

    def test_summary_request_uses_every_parent_in_single_document(self):
        self.pipeline.doc_service.list_documents.return_value = [self.document]

        context = self.pipeline._document_summary_context(
            "What are the main points of this document?"
        )

        self.assertEqual(len(context), 2)
        self.assertEqual(
            [item.compressed_text for item in context],
            [parent.text for parent in self.document.parent_chunks],
        )
        self.assertEqual(
            [item.matched_child.child_id for item in context],
            ["child-1", "child-2"],
        )

    def test_execute_chat_passes_summary_context_to_generator(self):
        self.pipeline.doc_service.list_documents.return_value = [self.document]
        self.pipeline.memory_store = Mock()
        self.pipeline.memory_store.extract_and_store.return_value = []
        self.pipeline.memory_store.get_user_memories.return_value = []
        self.pipeline.memory_store.build_persona_prompt.return_value = ""
        self.pipeline.compressor = Mock()
        self.pipeline.generator = Mock()
        self.pipeline.generator.generate.return_value = ("Summary answer", [], [])

        response = self.pipeline.execute_chat(
            "What are the main points of this document?"
        )

        self.pipeline.compressor.rerank_and_compress.assert_not_called()
        documents = self.pipeline.generator.generate.call_args.kwargs["documents"]
        self.assertEqual(len(documents), 2)
        self.assertEqual(response.answer, "Summary answer")
        self.assertEqual(len(response.retrieved_context), 2)

    def test_summary_request_can_select_a_named_document(self):
        other_document = DocumentRecord(
            document_id="doc-2",
            filename="Other.pdf",
            file_type="pdf",
            file_size_bytes=100,
            char_count=20,
        )
        self.pipeline.doc_service.list_documents.return_value = [
            self.document,
            other_document,
        ]

        context = self.pipeline._document_summary_context(
            "Summarize Project_Documentation.pdf"
        )

        self.assertEqual(len(context), 2)
        self.assertTrue(
            all(item.parent_chunk.document_id == "doc-1" for item in context)
        )

    def test_summary_request_does_not_guess_between_multiple_documents(self):
        self.pipeline.doc_service.list_documents.return_value = [
            self.document,
            DocumentRecord(
                document_id="doc-2",
                filename="Other.pdf",
                file_type="pdf",
                file_size_bytes=100,
                char_count=20,
            ),
        ]

        context = self.pipeline._document_summary_context(
            "What are the main points of this document?"
        )

        self.assertIsNone(context)


if __name__ == "__main__":
    unittest.main()
