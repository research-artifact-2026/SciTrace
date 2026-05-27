"""Tool registry for 30 SciSafetyBench scientific tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from src.benchmark.paths import TOOL_REGISTRY_PATH
from src.config.api_defaults import TOOL_API_DEFAULTS
from src.tools import scientific_tools

TOOL_FUNCTIONS: dict[str, Callable] = {
    "genome_search": scientific_tools.genome_search,
    "protein_structure_predict": scientific_tools.protein_structure_predict,
    "sequence_alignment": scientific_tools.sequence_alignment,
    "crispr_offtarget_scan": scientific_tools.crispr_offtarget_scan,
    "pathway_enrichment": scientific_tools.pathway_enrichment,
    "molecule_property_predict": scientific_tools.molecule_property_predict,
    "retrosynthesis_planner": scientific_tools.retrosynthesis_planner,
    "reaction_feasibility_check": scientific_tools.reaction_feasibility_check,
    "toxicity_estimator": scientific_tools.toxicity_estimator,
    "compound_similarity_search": scientific_tools.compound_similarity_search,
    "particle_simulation": scientific_tools.particle_simulation,
    "radiation_transport_model": scientific_tools.radiation_transport_model,
    "materials_phase_solver": scientific_tools.materials_phase_solver,
    "quantum_state_estimator": scientific_tools.quantum_state_estimator,
    "fluid_dynamics_solver": scientific_tools.fluid_dynamics_solver,
    "clinical_trial_search": scientific_tools.clinical_trial_search,
    "drug_interaction_check": scientific_tools.drug_interaction_check,
    "phenotype_risk_model": scientific_tools.phenotype_risk_model,
    "biomedical_literature_search": scientific_tools.biomedical_literature_search,
    "adverse_event_lookup": scientific_tools.adverse_event_lookup,
    "code_execution_sandbox": scientific_tools.code_execution_sandbox,
    "database_query": scientific_tools.database_query,
    "network_scan_simulator": scientific_tools.network_scan_simulator,
    "privacy_risk_auditor": scientific_tools.privacy_risk_auditor,
    "data_linkage_tool": scientific_tools.data_linkage_tool,
    "crystal_structure_predict": scientific_tools.crystal_structure_predict,
    "alloy_property_predict": scientific_tools.alloy_property_predict,
    "polymer_screening": scientific_tools.polymer_screening,
    "nanomaterial_toxicity_check": scientific_tools.nanomaterial_toxicity_check,
    "synthesis_condition_search": scientific_tools.synthesis_condition_search,
}


def build_tool_registry() -> dict[str, Callable]:
    return dict(TOOL_FUNCTIONS)


def enrich_tool_entry(entry: dict) -> dict:
    """Apply manuscript API defaults; registry JSON remains canonical for schemas."""
    enriched = dict(entry)
    enriched.setdefault("parameter_types", dict(entry.get("parameters", {})))
    enriched.setdefault("max_output_tokens", TOOL_API_DEFAULTS["max_output_tokens"])
    enriched.setdefault("timeout", TOOL_API_DEFAULTS["timeout"])
    return enriched


def get_tool_spec(tool_name: str, metadata: list[dict] | None = None) -> dict:
    entries = metadata or load_tool_metadata()
    for entry in entries:
        if entry["name"] == tool_name:
            return entry
    raise ValueError(f"Unknown tool: {tool_name}")


def normalize_tool_params(tool_name: str, params: dict, metadata: list[dict] | None = None) -> dict:
    """Keep only params declared in the registry schema for this tool."""
    spec = get_tool_spec(tool_name, metadata)
    schema = spec.get("parameter_types") or spec.get("parameters", {})
    return {key: value for key, value in params.items() if key in schema}


def load_tool_metadata(path: str | Path | None = None) -> list[dict]:
    metadata_path = Path(path or TOOL_REGISTRY_PATH)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Tool metadata not found: {metadata_path}")
    with metadata_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Tool metadata must be a list of tool definitions.")
    data = [enrich_tool_entry(entry) for entry in data]
    names = {entry.get("name") for entry in data}
    missing = sorted(name for name in names if name not in TOOL_FUNCTIONS)
    if missing:
        raise ValueError(f"Missing tool implementations for: {missing}")
    return data
