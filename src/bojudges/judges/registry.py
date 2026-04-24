from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from bojudges.judges.base import Judge, load_exemplars_file, load_persona_file

log = logging.getLogger("bojudges.registry")


class _ManifestJudge(Judge):
    """Judge instantiated from an on-disk manifest directory."""


class JudgeRegistry:
    def __init__(self, judges: list[Judge] | None = None) -> None:
        self.judges: list[Judge] = judges or []

    def add(self, judge: Judge) -> None:
        self.judges.append(judge)

    def __iter__(self) -> Iterable[Judge]:
        return iter(self.judges)

    def __len__(self) -> int:
        return len(self.judges)

    def by_id(self, judge_id: str) -> Judge | None:
        for j in self.judges:
            if j.id == judge_id:
                return j
        return None

    @classmethod
    def from_dir(cls, root: Path) -> JudgeRegistry:
        reg = cls()
        if not root.exists():
            return reg
        for manifest_path in sorted(root.rglob("manifest.yaml")):
            try:
                judge = load_judge_from_manifest(manifest_path)
                reg.add(judge)
            except Exception as e:
                log.warning("failed to load judge at %s: %s", manifest_path, e)
        return reg


def load_judge_from_manifest(manifest_path: Path) -> Judge:
    spec = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    root = manifest_path.parent
    persona_file = root / spec.get("persona_file", "persona.md")
    exemplars_file = root / spec.get("exemplars_file", "exemplars.jsonl")

    _persona_text = load_persona_file(persona_file) if persona_file.exists() else ""
    _exemplars = load_exemplars_file(exemplars_file)
    _tools = _build_tools(spec.get("tools") or [])
    calib = spec.get("calibration") or {}

    _calibration_temperature = (
        float(calib["temperature"]) if calib.get("temperature") is not None else None
    )
    _calibration_reliability = dict(calib.get("reliability") or {})

    class _Loaded(_ManifestJudge):
        id = str(spec.get("id", ""))
        name = str(spec.get("name", ""))
        tier = int(spec.get("tier", 2))
        tags = list(spec.get("tags") or [])
        risk_tags = list(spec.get("risk_tags") or [])
        model_id = str(spec.get("model", "claude-sonnet-4-6"))
        default_tools = _tools
        exemplars = _exemplars
        calibration_temperature = _calibration_temperature
        calibration_reliability = _calibration_reliability

        def persona_prompt(self) -> str:
            return _persona_text

    if not _Loaded.id:
        raise ValueError(f"manifest at {manifest_path} missing 'id'")
    if not _Loaded.name:
        raise ValueError(f"manifest at {manifest_path} missing 'name'")

    return _Loaded()


def _build_tools(specs: list[Any]) -> list:
    tools = []
    for s in specs:
        name = s if isinstance(s, str) else s.get("name")
        opts = {} if isinstance(s, str) else {k: v for k, v in s.items() if k != "name"}
        if name == "semgrep":
            from bojudges.tools.semgrep import SemgrepTool

            tools.append(SemgrepTool(**opts))
        elif name:
            log.warning("unknown tool %r in manifest; skipping", name)
    return tools


def load_builtin_judges() -> JudgeRegistry:
    """Load judges from the packaged `judges/builtin/` directory."""
    here = Path(__file__).parent / "builtin"
    return JudgeRegistry.from_dir(here)
