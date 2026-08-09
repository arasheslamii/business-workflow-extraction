"""Typed-ish config loader. Fails loudly on missing keys rather than
defaulting, so a typo in config.yaml stops the run instead of silently
changing the experiment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


class Config:
    def __init__(self, data: dict[str, Any], root: Path = ROOT):
        self._d = data
        self.root = root

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        p = Path(path) if path else ROOT / "config.yaml"
        if not p.exists():
            raise FileNotFoundError(f"config not found: {p}")
        return cls(yaml.safe_load(p.read_text()))

    def get(self, dotted: str) -> Any:
        cur: Any = self._d
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise KeyError(f"config key not found: {dotted!r} (at {part!r})")
            cur = cur[part]
        return cur

    def path(self, dotted: str) -> Path:
        """Resolve a configured path against the repo root."""
        return (self.root / str(self.get(dotted))).resolve()

    def as_dict(self) -> dict[str, Any]:
        return self._d
