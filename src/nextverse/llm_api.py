"""Cached, rate-limited Gemini client for the LLM-as-judge layer.

Design constraints that drove this:
  - Reproducibility. Judge verdicts must survive re-running the report. Every
    response is cached to disk keyed by a hash of (model, prompt, generation
    settings), so re-running costs nothing and produces identical results.
  - Resumability. A run that dies at call 250/280 must not restart from zero;
    the cache is written per call, not at the end.
  - Rate limits. Free-tier Gemini quotas are low. We pace requests and retry
    429/5xx with exponential backoff rather than dying.

Cost/idempotency note: the cache key deliberately EXCLUDES nothing that affects
the output. Changing the prompt or the model produces a new key, so a stale
verdict can never be silently reused.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any


class JudgeError(RuntimeError):
    pass


def cache_key(model: str, prompt: str, settings: dict[str, Any]) -> str:
    blob = json.dumps(
        {"model": model, "prompt": prompt, "settings": settings},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


class GeminiClient:
    def __init__(
        self,
        model: str,
        cache_dir: Path,
        *,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_output_tokens: int = 2048,
        min_interval_s: float = 1.0,
        max_retries: int = 6,
    ):
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.settings = {
            "temperature": temperature,   # 0.0: the judge should be as
                                          # deterministic as the API allows
            "max_output_tokens": max_output_tokens,
        }
        self.min_interval_s = min_interval_s
        self.max_retries = max_retries
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._client = None
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.stats = {"cache_hits": 0, "api_calls": 0, "retries": 0}

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise JudgeError(
                "GEMINI_API_KEY is not set in this environment. "
                "Export it (it lives in ~/.bashrc) before running the judge."
            )
        from google import genai

        self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _cache_path(self, key: str) -> Path:
        # Two-level fan-out: a few hundred files in one directory is fine, but
        # this keeps the tree tidy if the eval set grows.
        return self.cache_dir / key[:2] / f"{key}.json"

    def generate(self, prompt: str, *, tag: str = "") -> str:
        key = cache_key(self.model, prompt, self.settings)
        path = self._cache_path(key)
        if path.exists():
            self.stats["cache_hits"] += 1
            return json.loads(path.read_text())["response"]

        client = self._ensure_client()
        from google.genai import types

        cfg = types.GenerateContentConfig(
            temperature=self.settings["temperature"],
            max_output_tokens=self.settings["max_output_tokens"],
        )

        delay = 2.0
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            with self._lock:
                gap = time.time() - self._last_call
                if gap < self.min_interval_s:
                    time.sleep(self.min_interval_s - gap)
                self._last_call = time.time()
            try:
                resp = client.models.generate_content(
                    model=self.model, contents=prompt, config=cfg
                )
                # Thinking models spend most of the output budget before writing
                # a token of answer. If the budget runs out the JSON is cut
                # mid-object and no amount of repair can recover it, so surface
                # it as a clear configuration error rather than a parse failure.
                cand = resp.candidates[0] if getattr(resp, "candidates", None) else None
                finish = str(getattr(cand, "finish_reason", "") or "")
                text = (resp.text or "").strip()
                if "MAX_TOKENS" in finish or (not text and "STOP" not in finish):
                    um = getattr(resp, "usage_metadata", None)
                    raise JudgeError(
                        f"judge response truncated (finish_reason={finish}, "
                        f"thinking_tokens={getattr(um, 'thoughts_token_count', '?')}, "
                        f"answer_tokens={getattr(um, 'candidates_token_count', '?')}). "
                        f"Raise judge.max_output_tokens above "
                        f"{self.settings['max_output_tokens']} in config.yaml."
                    )
                if not text:
                    raise JudgeError(f"empty response from judge (finish_reason={finish})")
                self.stats["api_calls"] += 1
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(
                        {
                            "model": self.model,
                            "settings": self.settings,
                            "tag": tag,
                            "prompt": prompt,
                            "response": text,
                            "ts": time.time(),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return text
            except Exception as e:  # noqa: BLE001 - retry on anything transient
                last_err = e
                msg = str(e).lower()
                transient = any(
                    s in msg
                    for s in ("429", "rate", "quota", "500", "503", "timeout", "unavailable")
                )
                if attempt == self.max_retries - 1 or not transient:
                    break
                self.stats["retries"] += 1
                print(f"    retry {attempt + 1}/{self.max_retries} in {delay:.0f}s: {e}")
                time.sleep(delay)
                delay = min(delay * 2, 60.0)

        raise JudgeError(f"judge call failed after {self.max_retries} attempts: {last_err}")
