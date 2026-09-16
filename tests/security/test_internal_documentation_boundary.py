from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_internal_documentation_agent_does_not_import_external_search_sdk() -> None:
    source_dir = ROOT / "src" / "ai_agents" / "internal_documentation_agent"
    forbidden = ("parallel", "google.genai", "openai", "ollama")

    for path in source_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text


def test_capability_is_read_only_by_contract() -> None:
    text = (
        ROOT
        / "src"
        / "ai_runtime"
        / "capabilities"
        / "internal_documentation_executor.py"
    ).read_text(encoding="utf-8")

    assert ".delete(" not in text
    assert ".update(" not in text
    assert ".write(" not in text
