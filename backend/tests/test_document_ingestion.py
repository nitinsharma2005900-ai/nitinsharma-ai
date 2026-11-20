import unittest
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from app.services.document_service import DocumentService
from app.rag.pipeline import rag_pipeline
from app.utils.text_parser import extract_text_from_file, extract_text_from_docx


class TestDocumentIngestion(unittest.TestCase):
    """Test suite for document ingestion across PDF, TXT, and DOCX formats."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_11_document_ingestion_txt_and_docx(self):
        """Test 11: Ingest text and docx files, verify chunk splitting and cleanup."""
        # 1. Test TXT Ingestion
        txt_file = self.temp_path / "architecture_spec.txt"
        content = (
            "Advanced RAG Agent Architecture Specification.\n\n"
            "The system employs hybrid search combining Cohere dense semantic embeddings "
            "with Okapi BM25 sparse lexical search. Merging is achieved via Reciprocal Rank Fusion (RRF).\n\n"
            "To preserve complete context, documents are chunked hierarchically into 1000-character "
            "parent blocks and 200-character child blocks. Child blocks are indexed in the vector store "
            "and BM25 dictionary. When a child matches a query, its parent document is retrieved.\n\n"
            "Finally, Cohere ReRank v3 evaluates the top 20 candidate parent nodes, filtering them down "
            "to the 5 most relevant documents and pruning unnecessary context before prompting Gemini."
        )
        txt_file.write_text(content, encoding="utf-8")

        record = rag_pipeline.ingest_document(txt_file, filename="architecture_spec.txt")

        self.assertEqual(record.filename, "architecture_spec.txt")
        self.assertEqual(record.file_type, "txt")
        self.assertGreater(len(record.parent_chunks), 0)

        # 2. Test DOCX Ingestion (synthesizing a valid minimal docx zip archive)
        docx_file = self.temp_path / "sample_manual.docx"
        with zipfile.ZipFile(docx_file, "w") as docx_zip:
            xml_data = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>'
                '<w:p><w:r><w:t>Mem0 Semantic Memory provides persistent user profiling.</w:t></w:r></w:p>'
                '<w:p><w:r><w:t>It records user facts and coding preferences across sessions.</w:t></w:r></w:p>'
                '</w:body>'
                '</w:document>'
            )
            docx_zip.writestr("word/document.xml", xml_data)

        parsed_text, ftype = extract_text_from_file(docx_file)
        self.assertEqual(ftype, "docx")
        self.assertIn("Mem0 Semantic Memory", parsed_text)

        # Ingest docx
        docx_record = rag_pipeline.ingest_document(docx_file, filename="sample_manual.docx")
        self.assertEqual(docx_record.file_type, "docx")

        # 3. Test Document Deletion
        del_success = rag_pipeline.delete_document(record.document_id)
        self.assertTrue(del_success)

        # Verify document is gone from document list
        remaining_docs = [d.document_id for d in rag_pipeline.doc_service.list_documents()]
        self.assertNotIn(record.document_id, remaining_docs)


if __name__ == "__main__":
    unittest.main()
