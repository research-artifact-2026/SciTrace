import importlib.util
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

MAIN_NAMES = [
    f"{backbone}_{method}"
    for backbone in ("llama31_70b", "qwen25_72b", "deepseekv3", "gpt4o")
    for method in ("bare", "safescientist", "scitrace")
]


def _load_run_single_config_module():
    path = ROOT / "scripts" / "run_single_config.py"
    spec = importlib.util.spec_from_file_location("run_single_config", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_main_yaml_configs_exist_and_parse():
    for name in MAIN_NAMES:
        ypath = ROOT / "experiments" / "configs" / f"{name}.yaml"
        assert ypath.is_file(), f"Missing {ypath}"
        data = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data.get("experiment_name") == name


def test_main_yaml_matches_paired_json():
    for name in MAIN_NAMES:
        jpath = ROOT / "experiments" / "configs" / "json" / f"{name}.json"
        ypath = ROOT / "experiments" / "configs" / f"{name}.yaml"
        jd = json.loads(jpath.read_text(encoding="utf-8"))
        yd = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        assert jd == yd


def test_load_raw_config_accepts_yaml():
    mod = _load_run_single_config_module()
    p = ROOT / "experiments" / "configs" / "qwen25_72b_scitrace.yaml"
    cfg = mod.load_raw_config(p)
    assert cfg["experiment_name"] == "qwen25_72b_scitrace"


def test_index_json_lists_existing_yaml_paths():
    idx = json.loads((ROOT / "experiments" / "index.json").read_text(encoding="utf-8"))
    for group in ("experiments", "ablations"):
        for entry in idx[group]:
            assert "config_yaml" in entry
            ypath = ROOT / entry["config_yaml"]
            assert ypath.is_file(), f"Missing {ypath}"


def test_index_yaml_exists_and_parses():
    path = ROOT / "experiments" / "index.yaml"
    assert path.is_file()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "experiments" in data and "ablations" in data
