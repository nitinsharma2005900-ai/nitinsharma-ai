import unittest
import asyncio
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch
from urllib.error import HTTPError
from pathlib import Path
from app.core.compat import ValidationError, HTTPException

from app.schemas.chat import ChatRequest
from app.rag.generator import GeminiGenerator
from app.rag.pipeline import rag_pipeline
from app.utils.text_parser import extract_text_from_file
from app.api.documents import delete_document


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling, validation, and missing API key behaviors."""

    def test_offline_generation_does_not_match_hi_inside_this(self):
        generator = GeminiGenerator()

        answer = generator._offline_generate(
            "What is this examination form for?", [], ""
        )

        self.assertIn("do not contain sufficient information", answer)

    def test_gemini_retries_transient_service_errors(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"candidates":[{"content":{"parts":[{"text":"Answer"}]}}]}'
        )
        service_unavailable = HTTPError(
            "https://example.test", 503, "Service Unavailable", None, None
        )

        with patch(
            "app.rag.generator.urllib.request.urlopen",
            side_effect=[service_unavailable, service_unavailable, response],
        ) as urlopen, patch("app.rag.generator.time.sleep") as sleep:
            answer = GeminiGenerator()._call_gemini_api("test prompt")

        self.assertEqual(answer, "Answer")
        self.assertEqual(urlopen.call_count, 3)
        sleep.assert_has_calls([call(1), call(2)])

    def test_general_knowledge_fallback_is_labeled_and_uncited(self):
        answer = (
            "General knowledge (not found in uploaded documents): "
            "An API defines how software systems communicate."
        )
        generator = GeminiGenerator()

        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "OFFLINE_TEST_MODE": "false"},
        ), patch.object(generator, "_call_gemini_api", return_value=answer) as call_api:
            result, sources, citations = generator.generate(
                "What is an API?", [], ""
            )

        self.assertIn("general knowledge", call_api.call_args.args[0].lower())
        self.assertEqual(result, answer)
        self.assertEqual(sources, [])
        self.assertEqual(citations, [])

    def test_live_prompt_includes_current_ist_time_and_requests_useful_detail(self):
        answer = (
            "General knowledge (not found in uploaded documents): "
            "It is 4:30 PM IST on Friday, November 20, 2026."
        )
        generator = GeminiGenerator()
        fixed_now = datetime(
            2026,
            11,
            20,
            16,
            30,
            tzinfo=timezone(timedelta(hours=5, minutes=30), name="IST"),
        )

        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "OFFLINE_TEST_MODE": "false"},
        ), patch(
            "app.rag.generator.datetime"
        ) as datetime_mock, patch.object(
            generator, "_call_gemini_api", return_value=answer
        ) as call_api:
            datetime_mock.now.return_value = fixed_now
            generator.generate(
                "What is the current date and time?",
                [],
            )

        prompt = call_api.call_args.args[0]
        self.assertIn("Friday, 20 November 2026, 04:30:00 PM IST", prompt)
        self.assertIn("UTC+05:30", prompt)
        self.assertIn("useful, well-developed answers", prompt)
        self.assertIn("Do not guess or claim you cannot access a clock", prompt)

    def test_12_empty_query_validation(self):
        """Test 12a: Verify empty query raises validation error."""
        with self.assertRaises((ValidationError, ValueError)):
            ChatRequest(query="", user_id="usr_99")

    def test_12_unsupported_file_type_rejection(self):
        """Test 12b: Verify unsupported file extension raises clean ValueError."""
        dummy_file = Path("malicious_script.exe")
        with self.assertRaises(ValueError) as ctx:
            extract_text_from_file(dummy_file)
        self.assertIn("Unsupported file type", str(ctx.exception))

    def test_12_delete_nonexistent_document(self):
        """Test 12c: Verify deleting non-existent document raises 404 HTTPException."""
        with self.assertRaises(HTTPException) as ctx:
            delete_document("non_existent_doc_id_9999")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_12_missing_keys_graceful_handling(self):
        """Test 12d: Verify missing API keys fall back to resilient offline mode instead of unhandled crash."""
        # Execute chat without live API keys
        response = rag_pipeline.execute_chat(
            query="Tell me about hybrid search",
            user_id="test_user_err",
            session_id="session_err",
        )
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.answer)
        self.assertGreater(response.telemetry.total_latency_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
