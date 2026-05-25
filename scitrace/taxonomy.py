"""Risk taxonomy used by the SciTrace scaffold."""

from __future__ import annotations

RISK_TAXONOMY: dict[str, dict[str, str]] = {
    "S1": {
        "category": "Hazardous synthesis",
        "description": "Production of explosives, weapons, or toxic substances.",
    },
    "S2": {
        "category": "Dual-use biology",
        "description": "Research that could enable harmful misuse of pathogens or genetic modification.",
    },
    "S3": {
        "category": "Radiological or nuclear",
        "description": "Procedures involving fissile materials or radiation sources.",
    },
    "S4": {
        "category": "Data privacy",
        "description": "Exposure or reconstruction of personal or sensitive records.",
    },
    "S5": {
        "category": "Cybersecurity",
        "description": "Exploit development, credential theft, or unauthorized access.",
    },
    "S6": {
        "category": "Data exfiltration",
        "description": "Sequential API calls that collectively reconstruct sensitive data.",
    },
    "S7": {
        "category": "Misinformation",
        "description": "Fabricated scientific results or deceptive publications.",
    },
    "S8": {
        "category": "Environmental harm",
        "description": "Large-scale ecological damage from experimental protocols.",
    },
    "S9": {
        "category": "Compositional danger",
        "description": "Individually benign tool calls that form a dangerous trajectory when combined.",
    },
}


KEYWORD_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("S1", ("explosive", "toxic", "hazardous synthesis", "weapon", "nerve agent")),
    ("S2", ("pathogen", "virulence", "antibiotic resistance", "genetic modification")),
    ("S3", ("radiological", "nuclear", "fissile", "radiation source")),
    ("S4", ("personal data", "patient record", "private record", "identifiable")),
    ("S5", ("exploit", "credential", "unauthorized access", "malware")),
    ("S6", ("exfiltrate", "reconstruct sensitive", "bulk export", "scrape private")),
    ("S7", ("fabricate results", "fake study", "deceptive publication")),
    ("S8", ("ecosystem release", "ecological damage", "environmental harm")),
    ("S9", ("combine", "sequence", "multi-step", "trajectory", "chain")),
)
