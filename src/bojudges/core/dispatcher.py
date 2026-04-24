from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from bojudges.core.panel import PanelItem
from bojudges.core.verifier import LineVerifier
from bojudges.judges.base import Judge, JudgeContext
from bojudges.providers.base import Provider
from bojudges.providers.registry import get_provider, resolve_model_provider
from bojudges.schema import JudgeVerdict

log = logging.getLogger("bojudges.dispatcher")


@dataclass
class DispatchConfig:
    max_workers: int = 6
    per_judge_timeout_sec: int = 180
    seed: int | None = None
    temperature: float = 0.3


class Dispatcher:
    """Runs a panel of judges in parallel, each in its own isolated LLM call.

    This is the actual "multi-agent" dispatch — one LLM call per judge, no
    shared context between judges, provider chosen by model_id.
    """

    def __init__(
        self,
        provider_factory: Callable[[str], Provider] | None = None,
        verifier: LineVerifier | None = None,
        config: DispatchConfig | None = None,
    ) -> None:
        self.provider_factory = provider_factory or _default_factory
        self.verifier = verifier or LineVerifier()
        self.config = config or DispatchConfig()

    def dispatch(self, panel: list[PanelItem], ctx: JudgeContext) -> list[JudgeVerdict]:
        verdicts: list[JudgeVerdict] = []
        if not panel:
            return verdicts

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            futures = {
                pool.submit(self._run_one, item.judge, ctx): item.judge
                for item in panel
            }
            for fut in as_completed(futures, timeout=None):
                judge = futures[fut]
                try:
                    v = fut.result(timeout=self.config.per_judge_timeout_sec)
                    verdicts.append(v)
                except Exception as e:
                    log.exception("judge %s failed", judge.id)
                    verdicts.append(self._failure_verdict(judge, str(e)))

        verdicts.sort(key=lambda v: (v.tier, v.judge_id))
        return verdicts

    def _run_one(self, judge: Judge, ctx: JudgeContext) -> JudgeVerdict:
        provider = self.provider_factory(judge.model_id)
        t0 = time.perf_counter()
        verdict = judge.review(
            provider=provider,
            ctx=ctx,
            verifier=self.verifier,
            seed=self.config.seed,
            temperature=self.config.temperature,
        )
        elapsed = int((time.perf_counter() - t0) * 1000)
        return verdict.model_copy(update={"duration_ms": elapsed})

    @staticmethod
    def _failure_verdict(judge: Judge, err: str) -> JudgeVerdict:
        from bojudges.schema import Verdict

        return JudgeVerdict(
            judge_id=judge.id,
            judge_name=judge.name,
            tier=judge.tier,
            verdict=Verdict.SKIP,
            score=0.0,
            confidence=0.0,
            core_finding=f"Judge errored: {err[:200]}",
            issues=[],
            tools_run=[],
            duration_ms=0,
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            model_id=judge.model_id,
            prompt_hash="",
            error=err,
        )


def _default_factory(model_id: str) -> Provider:
    return get_provider(resolve_model_provider(model_id))
