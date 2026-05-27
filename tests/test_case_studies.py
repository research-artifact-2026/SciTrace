import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = {
    "figure", "title", "domain", "task_summary", "call_sequence",
    "safe_scientist_behavior", "scitrace_behavior", "ctv_flagged_step",
    "ts_flow_feedback", "takeaway",
}

APPENDIX_L_REQUIRED_FIELDS = {
    "figure", "title", "section", "source_file", "template_type",
    "system_prompt", "user_template", "notes",
}


def test_case_studies_figures_9_to_12_exist():
    for filename in [
        "figure9_biology_case.json",
        "figure10_chemistry_case.json",
        "figure11_info_sci_case.json",
        "figure12_medicine_case.json",
    ]:
        path = ROOT / "data/case_studies" / filename
        assert path.exists(), f"Missing {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert REQUIRED_FIELDS.issubset(data.keys())


def test_case_studies_figures_13_to_16_appendix_l_templates_exist():
    for filename in [
        "figure13_appendix_l_sir_thinker_prompt_case.json",
        "figure14_appendix_l_sir_reviewer_prompt_case.json",
        "figure15_appendix_l_ctv_verification_prompt_case.json",
        "figure16_appendix_l_ts_flow_feedback_prompt_case.json",
    ]:
        path = ROOT / "data/case_studies" / filename
        assert path.exists(), f"Missing {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert APPENDIX_L_REQUIRED_FIELDS.issubset(data.keys())
        assert data["section"] == "Appendix L"
        assert data["source_file"].startswith("scitrace/")
        assert data["system_prompt"].strip()
        assert data["user_template"].strip()


def test_case_studies_exclude_operational_hazard_text():
    for path in (ROOT / "data/case_studies").glob("*.json"):
        text = path.read_text(encoding="utf-8").lower()
        for phrase in ["step-by-step synthesis", "exact protocol", "exploit code", "real patient", "operational parameter"]:
            assert phrase not in text
