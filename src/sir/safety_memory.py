"""AGrail-style keyword-overlap safety memory."""

from __future__ import annotations


def _tokenize(text: str) -> set[str]:
    """Whitespace-tokenize text for Jaccard overlap."""
    return {token.lower() for token in text.split() if token.strip()}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


_BUILTIN_CHECKS: list[tuple[str, str]] = [
    (
        "pathogen genome query",
        "Check dual-use biology (S2): confirm organism is non-pathogenic or educational only.",
    ),
    (
        "crispr gene drive design",
        "Check dual-use biology (S2) and environmental harm (S8): reject population-scale drives.",
    ),
    (
        "antibiotic resistance mechanism",
        "Check dual-use biology (S2): limit to aggregate resistance statistics, not enhancement.",
    ),
    (
        "chemical synthesis route",
        "Check hazardous synthesis (S1): block operational precursors or stepwise instructions.",
    ),
    (
        "energetic material formulation",
        "Check hazardous synthesis (S1): allow only high-level hazard classes.",
    ),
    (
        "radiation transport simulation",
        "Check radiological/nuclear (S3): use toy materials and non-operational summaries.",
    ),
    (
        "clinical cohort phenotype",
        "Check data privacy (S4): require de-identified aggregate cohorts only.",
    ),
    (
        "patient record linkage",
        "Check data privacy (S4) and exfiltration (S6): block re-identification workflows.",
    ),
    (
        "database query sensitive records",
        "Check data exfiltration (S6): restrict to de-identified aggregate tables.",
    ),
    (
        "network vulnerability scan",
        "Check cybersecurity (S5): use sandbox simulators with toy targets only.",
    ),
    (
        "model inversion attack",
        "Check cybersecurity (S5) and privacy (S4): block membership inference on private data.",
    ),
    (
        "misinformation scientific claim",
        "Check misinformation (S7): verify citations and reject fabricated results.",
    ),
    (
        "ecosystem disruption experiment",
        "Check environmental harm (S8): require containment and ethical review framing.",
    ),
    (
        "tool chain compositional trajectory",
        "Check compositional danger (S9): evaluate full call history, not isolated calls.",
    ),
    (
        "retrosynthesis controlled substance",
        "Check hazardous synthesis (S1) and compositional danger (S9): no actionable routes.",
    ),
    (
        "protein structure pathogen target",
        "Check dual-use biology (S2) and compositional danger (S9): redirect to toy proteins.",
    ),
    (
        "nanomaterial toxicity screening",
        "Check environmental harm (S8): return broad safety classes only.",
    ),
    (
        "adversarial jailbreak prompt",
        "Check misinformation (S7) and cybersecurity (S5): reject constraint overrides.",
    ),
    (
        "bulk data export pipeline",
        "Check data exfiltration (S6): cap exports to aggregate statistics.",
    ),
    (
        "nuclear criticality estimate",
        "Check radiological/nuclear (S3): educational summaries without operational parameters.",
    ),
]


class SafetyMemory:
    """Keyword-overlap memory for retrieving prior safety checks."""

    def __init__(self) -> None:
        self._entries: list[dict] = []
        for action, template in _BUILTIN_CHECKS:
            self.add(action, template)

    def add(self, action_description: str, check_template: str) -> None:
        """Store a safety check keyed by action description."""
        self._entries.append(
            {
                "action": action_description,
                "template": check_template,
                "tokens": _tokenize(action_description + " " + check_template),
            }
        )

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Return top-k check templates by Jaccard overlap with query."""
        if not self._entries or k <= 0:
            return []

        query_tokens = _tokenize(query)
        scored = [
            (_jaccard(query_tokens, entry["tokens"]), entry["template"])
            for entry in self._entries
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [template for score, template in scored[:k] if score > 0]

    def to_dict(self) -> dict:
        """Serialize memory entries."""
        return {
            "entries": [
                {"action": entry["action"], "template": entry["template"]}
                for entry in self._entries
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SafetyMemory":
        """Restore memory from serialized data."""
        memory = cls()
        memory._entries = []
        for entry in data.get("entries", []):
            memory.add(entry["action"], entry["template"])
        return memory
