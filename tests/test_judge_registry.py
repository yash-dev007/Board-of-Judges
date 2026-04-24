from __future__ import annotations

from bojudges.judges import load_builtin_judges


def test_builtin_has_sec_appsec_injection():
    registry = load_builtin_judges()
    judge = registry.by_id("sec-appsec-injection")
    assert judge is not None
    assert judge.tier == 1
    assert "security" in judge.tags
    assert judge.persona_prompt().startswith("You are a staff Application Security")
    assert len(judge.exemplars) >= 2
