import importlib.util
from pathlib import Path


def _load_streaming_app_module():
    repo_root = Path(__file__).resolve().parents[4]
    app_path = repo_root / "source" / "apps" / "02_llm_streaming_api" / "main.py"
    spec = importlib.util.spec_from_file_location("streaming_app_main", app_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_streaming_app_resolves_repo_root_and_samples():
    module = _load_streaming_app_module()

    assert module.REPO_ROOT.name == "ai_application"
    assert module.SAMPLES_PATH.is_file()
    assert module.INDEX_PATH.is_file()
    assert module._load_sample("S2")["id"] == "S2"
