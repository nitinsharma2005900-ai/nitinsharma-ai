import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Enable offline test mode for test runs
os.environ["OFFLINE_TEST_MODE"] = "true"
os.environ["GEMINI_API_KEY"] = ""
os.environ["COHERE_API_KEY"] = ""
os.environ["MEM0_API_KEY"] = ""


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Isolate storage and upload paths for test execution."""
    test_storage = tmp_path / "storage"
    test_uploads = tmp_path / "uploads"
    test_storage.mkdir(parents=True, exist_ok=True)
    test_uploads.mkdir(parents=True, exist_ok=True)

    from app.core.config import settings
    monkeypatch.setattr(settings, "STORAGE_DIR", test_storage)
    monkeypatch.setattr(settings, "UPLOAD_DIR", test_uploads)
    monkeypatch.setattr(settings, "DOC_STORE_PATH", test_storage / "docstore.json")
    monkeypatch.setattr(settings, "MEMORY_STORE_PATH", test_storage / "memories.json")
    monkeypatch.setattr(settings, "VECTOR_STORE_PATH", test_storage / "vector_store.json")
    monkeypatch.setenv("OFFLINE_TEST_MODE", "true")

    from app.rag.pipeline import rag_pipeline
    rag_pipeline.__init__()
