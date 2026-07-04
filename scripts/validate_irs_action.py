"""Validate LAMI IRS control actions against bounded trustworthiness rules."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import pandas as pd
from jsonschema import Draft202012Validator

from common import ROOT, ensure_dir, load_yaml, read_jsonl, save_csv


def validate_action(action: Dict, cfg: Dict, schema: Dict) -> Dict:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(action), key=lambda e: e.path)
    failed = []
    if errors:
        failed.extend(["schema:" + "/".join(str(x) for x in err.path) for err in errors])

    region_count = int(cfg["irs"]["region_count"])
    max_changed = max(1, int(region_count * float(cfg["irs"]["max_changed_fraction_per_interval"])))
    llm_thr = float(cfg["controller"]["llm_confidence_threshold"])

    phase_delta = action.get("phase_delta_code", [])
    if len(phase_delta) != region_count:
        failed.append("dimension_mismatch")
    if any(x not in (-1, 0, 1) for x in phase_delta):
        failed.append("invalid_phase_delta")
    if sum(1 for x in phase_delta if x != 0) > max_changed:
        failed.append("too_many_region_updates")
    if float(action.get("confidence", 0.0)) < llm_thr and not action.get("fallback_required", False):
        failed.append("low_llm_confidence_without_fallback")
    if action.get("fallback_required", False) and any(x != 0 for x in phase_delta):
        failed.append("fallback_contains_nonzero_update")
    if any(r < 0 or r >= region_count for r in action.get("target_regions", [])):
        failed.append("target_region_out_of_range")

    return {
        "record_id": action.get("record_id", -1),
        "client_id": action.get("client_id", "unknown"),
        "control_mode": action.get("control_mode", "unknown"),
        "validation_status": "VALID" if not failed else "INVALID",
        "safe_to_actuate": not failed,
        "failed_checks": ";".join(failed),
        "recommended_action": "apply" if not failed else "fallback_safe",
    }


def run(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    schema_path = ROOT / "schemas" / "llm_output_schema.json"
    schema = __import__("json").loads(schema_path.read_text(encoding="utf-8"))
    in_path = ROOT / cfg["output"]["sample_data_dir"] / "sample_irs_outputs.jsonl"
    if not in_path.exists():
        raise FileNotFoundError(f"Missing {in_path}. Run lami_reference_controller.py first.")
    actions = read_jsonl(in_path)
    results = [validate_action(a, cfg, schema) for a in actions]
    out_dir = ensure_dir(cfg["output"]["results_dir"])
    out_path = out_dir / "validation_results.csv"
    save_csv(pd.DataFrame(results), out_path)
    n_valid = sum(r["safe_to_actuate"] for r in results)
    print(f"Wrote {out_path}; valid actions: {n_valid}/{len(results)}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default_simulation.yaml")
    args = parser.parse_args()
    run(args.config)
