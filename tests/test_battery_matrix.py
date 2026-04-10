from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.battery import dispatch_expert, load_expert_profiles


def test_load_expert_profiles_reads_yaml(tmp_path: Path) -> None:
    config = tmp_path / "battery_matrix.yaml"
    config.write_text(
        'experts:\n'
        '  - name: "base-expert"\n'
        '    domain: "general"\n'
        '    description: "General planning"\n'
        '    model: "gemma4:31b"\n'
        '    adapter: "adapter-path"\n'
        '    privacy_sensitive: false\n'
        '    confidence_bias: 0.1\n'
        '    keywords:\n'
        '      - "plan"\n'
        '      - "summary"\n',
        "utf-8",
    )
    experts = load_expert_profiles(config)
    assert len(experts) == 1
    assert experts[0].name == "base-expert"
    assert experts[0].keywords == ["plan", "summary"]


def test_dispatch_expert_prefers_code_expert() -> None:
    experts = [
        type("Expert", (), {
            "name": "base-expert",
            "domain": "general",
            "description": "",
            "model": "gemma4:31b",
            "adapter": None,
            "privacy_sensitive": False,
            "keywords": ["plan", "summary"],
            "confidence_bias": 0.1,
        })(),
        type("Expert", (), {
            "name": "code-expert",
            "domain": "code",
            "description": "",
            "model": "gemma4:31b",
            "adapter": None,
            "privacy_sensitive": False,
            "keywords": ["code", "python", "bug", "patch"],
            "confidence_bias": 0.15,
        })(),
    ]
    dispatch = dispatch_expert("debug this python code patch", experts, confidence_threshold=0.4)
    assert dispatch.primary_expert.name == "code-expert"
    assert dispatch.cloud_assist_recommended is False


def test_dispatch_expert_prefers_privacy_expert_for_sensitive_task() -> None:
    experts = [
        type("Expert", (), {
            "name": "base-expert",
            "domain": "general",
            "description": "",
            "model": "gemma4:31b",
            "adapter": None,
            "privacy_sensitive": False,
            "keywords": ["plan", "summary"],
            "confidence_bias": 0.1,
        })(),
        type("Expert", (), {
            "name": "privacy-expert",
            "domain": "private",
            "description": "",
            "model": "gemma4:31b",
            "adapter": None,
            "privacy_sensitive": True,
            "keywords": ["private", "personal", "sensitive"],
            "confidence_bias": 0.05,
        })(),
    ]
    dispatch = dispatch_expert(
        "organize my private personal notes",
        experts,
        confidence_threshold=0.4,
        privacy_sensitive=True,
    )
    assert dispatch.primary_expert.name == "privacy-expert"


def test_dispatch_expert_prefers_logic_expert_for_reasoning_task() -> None:
    experts = [
        type("Expert", (), {
            "name": "base-expert",
            "domain": "general",
            "description": "",
            "model": "gemma4:31b",
            "adapter": None,
            "privacy_sensitive": False,
            "keywords": ["summary", "write"],
            "confidence_bias": 0.1,
        })(),
        type("Expert", (), {
            "name": "logic-expert",
            "domain": "reasoning",
            "description": "",
            "model": "gemma4:31b",
            "adapter": None,
            "privacy_sensitive": False,
            "keywords": ["logic", "math", "proof", "architecture", "system"],
            "confidence_bias": 0.15,
        })(),
    ]
    dispatch = dispatch_expert("design a system architecture proof with logic", experts)
    assert dispatch.primary_expert.name == "logic-expert"
