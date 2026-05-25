"""Simple session-local safety-check retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .taxonomy import RISK_TAXONOMY

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


@dataclass
class SafetyCheck:
    title: str
    category: str
    text: str


@dataclass
class SafetyMemory:
    """Retrieves relevant safety checks by deterministic token overlap."""

    checks: list[SafetyCheck] = field(default_factory=list)

    @classmethod
    def with_default_checks(cls) -> "SafetyMemory":
        checks = [
            SafetyCheck(
                title=f"{code} {item['category']}",
                category=code,
                text=item["description"],
            )
            for code, item in RISK_TAXONOMY.items()
        ]
        checks.extend(
            [
                SafetyCheck(
                    title="Cross-stage warning propagation",
                    category="S9",
                    text="Carry earlier warnings into later experiment and writing stages.",
                ),
                SafetyCheck(
                    title="Safer scientific redirection",
                    category="S9",
                    text="When a call is risky, redirect to non-sensitive examples or aggregate public data.",
                ),
            ]
        )
        return cls(checks=checks)

    def retrieve(self, query: str, k: int = 3) -> list[SafetyCheck]:
        query_tokens = tokenize(query)
        scored: list[tuple[int, SafetyCheck]] = []
        for check in self.checks:
            score = len(query_tokens & tokenize(f"{check.title} {check.text}"))
            if score:
                scored.append((score, check))
        scored.sort(key=lambda item: (-item[0], item[1].title))
        return [check for _, check in scored[:k]]
