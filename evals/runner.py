"""Eval harness — runs a given judge against a dataset and reports metrics.

Usage:
    python evals/runner.py --dataset sqli_seed --judge sec-appsec-injection
    python evals/runner.py --dataset sqli_seed --judge sec-appsec-injection --provider mock

Outputs a JSON report and prints a summary table.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bojudges.core.verifier import LineVerifier  # noqa: E402
from bojudges.judges import load_builtin_judges  # noqa: E402
from bojudges.judges.base import JudgeContext  # noqa: E402
from bojudges.providers.base import Provider  # noqa: E402
from bojudges.providers.registry import get_provider, resolve_model_provider  # noqa: E402
from bojudges.schema import Issue, JudgeVerdict  # noqa: E402


@dataclass
class EvalCase:
    file: str
    language: str
    expected_verdict: str
    expected_issues: list[dict[str, Any]]
    path: Path
    content: str
    tricky_notes: str = ""


@dataclass
class CaseResult:
    case: EvalCase
    verdict: JudgeVerdict
    true_positives: int
    false_positives: int
    false_negatives: int
    expected_verdict_correct: bool


def load_dataset(dataset_dir: Path) -> tuple[dict[str, Any], list[EvalCase]]:
    gt = yaml.safe_load((dataset_dir / "ground_truth.yaml").read_text(encoding="utf-8"))
    snippets_dir = dataset_dir / "snippets"
    cases: list[EvalCase] = []
    for entry in gt.get("snippets", []):
        p = snippets_dir / entry["file"]
        cases.append(
            EvalCase(
                file=entry["file"],
                language=entry.get("language", "python"),
                expected_verdict=entry["verdict"],
                expected_issues=entry.get("issues") or [],
                path=p,
                content=p.read_text(encoding="utf-8"),
                tricky_notes=entry.get("tricky_notes", ""),
            )
        )
    return gt, cases


def match_issue(pred: Issue, expected: dict[str, Any], window: int = 3) -> bool:
    if expected.get("category") and expected["category"] != pred.category:
        return False
    ex_line = expected.get("line")
    return not (ex_line is not None and abs((pred.line or 0) - ex_line) > window)


def score_case(case: EvalCase, verdict: JudgeVerdict) -> CaseResult:
    verified = [i for i in verdict.issues if i.verified]
    unmatched_expected = list(case.expected_issues)
    tp = 0
    fp = 0
    for pred in verified:
        hit = None
        for ex in unmatched_expected:
            if match_issue(pred, ex):
                hit = ex
                break
        if hit is not None:
            tp += 1
            unmatched_expected.remove(hit)
        else:
            fp += 1
    fn = len(unmatched_expected)

    expected_correct = verdict.verdict.value == case.expected_verdict

    return CaseResult(
        case=case,
        verdict=verdict,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        expected_verdict_correct=expected_correct,
    )


def aggregate(results: list[CaseResult]) -> dict[str, Any]:
    tp = sum(r.true_positives for r in results)
    fp = sum(r.false_positives for r in results)
    fn = sum(r.false_negatives for r in results)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    verdict_acc = sum(r.expected_verdict_correct for r in results) / max(len(results), 1)

    ece = _compute_ece(results)

    return {
        "cases": len(results),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "verdict_accuracy": round(verdict_acc, 3),
        "ece": round(ece, 3),
        "errored": sum(1 for r in results if r.verdict.error),
    }


def _compute_ece(results: list[CaseResult], n_bins: int = 5) -> float:
    """Expected Calibration Error: |average_confidence - accuracy| per bin, weighted."""
    if not results:
        return 0.0
    bins: list[list[CaseResult]] = [[] for _ in range(n_bins)]
    for r in results:
        conf = r.verdict.confidence
        idx = min(int(conf * n_bins), n_bins - 1)
        bins[idx].append(r)
    ece = 0.0
    n_total = len(results)
    for bucket in bins:
        if not bucket:
            continue
        avg_conf = sum(r.verdict.confidence for r in bucket) / len(bucket)
        acc = sum(r.expected_verdict_correct for r in bucket) / len(bucket)
        ece += (len(bucket) / n_total) * abs(avg_conf - acc)
    return ece


def mock_provider_for(cases: list[EvalCase]) -> Provider:
    """Return a MockProvider scripted to produce the expected verdict for each
    seed case. Used when running without real API keys — lets the harness
    validate end-to-end plumbing.
    """
    from bojudges.providers.base import ToolCall
    from bojudges.providers.mock import MockProvider, ScriptedResponse

    def handler(messages, model: str) -> ScriptedResponse:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        matched: EvalCase | None = None
        # Match on the full content so files with identical first lines
        # (e.g. `import subprocess`) can't collide.
        for case in cases:
            # content is wrapped + guarded in the prompt; check a unique substring
            stripped = case.content.strip()
            if not stripped:
                continue
            # Prefer a longer unique substring: last ~120 chars of content.
            unique = stripped[-120:] if len(stripped) > 120 else stripped
            if unique in last_user:
                matched = case
                break
        if matched is None:
            for case in cases:
                if case.content.strip() in last_user:
                    matched = case
                    break

        if matched is None:
            payload = {
                "verdict": "PASS",
                "score": 7,
                "confidence": 0.5,
                "core_finding": "mock default",
                "issues": [],
            }
        elif matched.expected_verdict == "PASS":
            payload = {
                "verdict": "PASS",
                "score": 9,
                "confidence": 0.85,
                "core_finding": f"mock PASS for {matched.file}",
                "issues": [],
            }
        else:
            issues = []
            for ex in matched.expected_issues:
                issues.append(
                    {
                        "severity": ex.get("severity", "HIGH"),
                        "title": f"Mock finding: {ex.get('category', 'issue')}",
                        "description": f"Ground-truth injection at line {ex.get('line')}",
                        "line": ex.get("line", 1),
                        "cwe": ex.get("cwe", ""),
                        "category": ex.get("category", "security"),
                        "fix_hint": "mock fix hint",
                        "confidence": 0.9,
                        "tool_citations": [],
                    }
                )
            payload = {
                "verdict": matched.expected_verdict,
                "score": 2,
                "confidence": 0.9,
                "core_finding": f"mock FAIL for {matched.file}",
                "issues": issues,
            }

        return ScriptedResponse(
            text=None,
            tool_calls=[ToolCall(id="t1", name="record_verdict", input=payload)],
        )

    return MockProvider(handler=handler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="sqli_seed")
    parser.add_argument("--judge", required=True)
    parser.add_argument(
        "--provider",
        default="auto",
        help="auto | mock | anthropic | google | openai",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--report",
        default=None,
        help="Path to write JSON report. Default: evals/reports/<dataset>_<judge>.json",
    )
    args = parser.parse_args()

    ds_dir = Path(__file__).resolve().parent / "datasets" / args.dataset
    gt_spec, cases = load_dataset(ds_dir)

    registry = load_builtin_judges()
    judge = registry.by_id(args.judge)
    if judge is None:
        print(f"judge not found: {args.judge}", file=sys.stderr)
        print("available:", [j.id for j in registry], file=sys.stderr)
        return 2

    if args.model:
        judge.model_id = args.model

    if args.provider == "mock":
        provider: Provider = mock_provider_for(cases)
    elif args.provider == "auto":
        provider = get_provider(resolve_model_provider(judge.model_id))
    else:
        provider = get_provider(args.provider)

    verifier = LineVerifier()
    results: list[CaseResult] = []
    for case in cases:
        ctx = JudgeContext(
            submission_path=str(case.path),
            submission_content=case.content,
            language=case.language,
        )
        verdict = judge.review(provider=provider, ctx=ctx, verifier=verifier)
        results.append(score_case(case, verdict))

    metrics = aggregate(results)

    report = {
        "dataset": gt_spec.get("dataset", args.dataset),
        "judge": judge.id,
        "model": judge.model_id,
        "provider": provider.name,
        "metrics": metrics,
        "cases": [
            {
                "file": r.case.file,
                "expected_verdict": r.case.expected_verdict,
                "predicted_verdict": r.verdict.verdict.value,
                "predicted_score": r.verdict.score,
                "predicted_confidence": r.verdict.confidence,
                "tp": r.true_positives,
                "fp": r.false_positives,
                "fn": r.false_negatives,
                "correct": r.expected_verdict_correct,
                "issues": [i.model_dump() for i in r.verdict.issues],
                "error": r.verdict.error,
            }
            for r in results
        ],
    }

    report_path = Path(args.report) if args.report else (
        Path(__file__).resolve().parent / "reports" / f"{args.dataset}_{judge.id}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 72)
    print(f"Dataset: {args.dataset}   Judge: {judge.id}   Model: {judge.model_id}")
    print(f"Provider: {provider.name}")
    print("-" * 72)
    for r in results:
        mark = "✓" if r.expected_verdict_correct else "✗"
        err = f"  ERROR: {r.verdict.error[:60]}" if r.verdict.error else ""
        print(
            f"  {mark}  {r.case.file:40s} "
            f"exp={r.case.expected_verdict:4s}  got={r.verdict.verdict.value:4s} "
            f"conf={r.verdict.confidence:.2f}  tp={r.true_positives} "
            f"fp={r.false_positives} fn={r.false_negatives}{err}"
        )
    print("-" * 72)
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall:    {metrics['recall']:.3f}")
    print(f"  F1:        {metrics['f1']:.3f}")
    print(f"  Verdict accuracy: {metrics['verdict_accuracy']:.3f}")
    print(f"  ECE:       {metrics['ece']:.3f}")
    print(f"  Errored cases: {metrics['errored']}")
    print(f"\nReport written to {report_path}")

    gate = args.dataset.endswith("_seed")
    if gate:
        passed = (
            metrics["precision"] >= 0.70
            and metrics["recall"] >= 0.60
            and metrics["ece"] <= 0.15
            and metrics["errored"] == 0
        )
        print("=" * 72)
        print("PHASE 0 GATE:", "PASS ✓" if passed else "FAIL ✗")
        return 0 if passed else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
