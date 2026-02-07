import importlib
import pathlib
import sys


def test_settings_exposes_rag_config(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    backend_dir = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_dir))
    try:
        from app import settings as settings_module

        importlib.reload(settings_module)
        settings = settings_module.settings

        assert settings.RAG_TOP_K == 4
        assert settings.CHROMA_DIR == "chroma_store"
        assert settings.KB_DIR == "knowledge_base"
    finally:
        sys.path.remove(str(backend_dir))
