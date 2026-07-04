"""Reference LAMI controller.

This is a deterministic surrogate for the bounded SLM-LLM IRS control path.
It maps semantic descriptors to JSON IRS control actions, then the validation
script can check whether each action is physically admissible.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np

from common import ROOT, ensure_dir, load_yaml, read_jsonl, write_jsonl


def decide_action(desc: Dict, cfg: Dict) -> Dict:
    ctrl = cfg["controller"]
    irs = cfg["irs"]
    region_count = int(irs["region_count"])
    slm_thr = float(ctrl["slm_confidence_threshold"])
    hint = int(desc.get("region_hint", 0)) % region_count
    phase_delta = [0] * region_count

    scores = desc["intent_scores"]
    coverage = float(scores["coverage_recovery"])
    suppression = float(scores["interference_suppression"])
    saving = float(scores["energy_saving"])
    slm_conf = float(desc["slm_confidence"])
    snr_trend = desc["snr_trend"]
    interference = float(desc["interference_db"])
    priority = int(desc["priority_level"])

    if slm_conf < slm_thr:
        return {
            "control_mode": "fallback_safe",
            "target_regions": [],
            "phase_delta_code": phase_delta,
            "confidence": round(min(slm_conf, 0.60), 3),
            "fallback_required": True,
            "reason_code": "low_slm_confidence",
        }

    # Weighted decision. The values are intentionally simple and auditable.
    coverage_score = coverage + 0.08 * priority + (0.12 if snr_trend == "decreasing" else 0.0)
    suppress_score = suppression + (0.15 if interference >= 4.0 else 0.0)
    saving_score = saving + (0.10 if snr_trend == "stable" else -0.10)

    if suppress_score >= max(coverage_score, saving_score) and suppress_score >= 0.55:
        mode = "interference_suppression"
        targets = sorted(set([hint, min(hint + 1, region_count - 1)]))
        for r in targets:
            phase_delta[r] = 1 if (r + priority) % 2 == 0 else -1
        confidence = min(0.97, 0.70 + 0.20 * suppression + 0.05 * slm_conf)
        reason = "localized_interference_high_confidence"
    elif coverage_score >= max(suppress_score, saving_score) and coverage_score >= 0.50:
        mode = "coverage_recovery"
        targets = [hint]
        phase_delta[hint] = 1
        confidence = min(0.96, 0.68 + 0.20 * coverage + 0.06 * slm_conf)
        reason = "snr_drop_or_priority_coverage_recovery"
    elif saving_score >= 0.60:
        mode = "hold_state"
        targets = []
        confidence = min(0.95, 0.72 + 0.15 * saving + 0.04 * slm_conf)
        reason = "stable_link_energy_saving"
    else:
        mode = "selective_update"
        targets = [hint]
        phase_delta[hint] = 1 if coverage >= suppression else -1
        confidence = min(0.92, 0.70 + 0.08 * max(coverage, suppression) + 0.05 * slm_conf)
        reason = "moderate_adaptation"

    action = {
        "control_mode": mode,
        "target_regions": targets,
        "phase_delta_code": phase_delta,
        "confidence": round(float(confidence), 3),
        "fallback_required": False,
        "reason_code": reason,
    }

    # The reference pipeline includes the LLM confidence gate before actuation.
    # Low-confidence candidate actions are converted to explicit fallback-safe outputs
    # so that the final command stream is safe for the downstream IRS validator.
    if action["confidence"] < float(ctrl["llm_confidence_threshold"]):
        return {
            "control_mode": "fallback_safe",
            "target_regions": [],
            "phase_delta_code": [0] * region_count,
            "confidence": 1.0,
            "fallback_required": True,
            "reason_code": "llm_confidence_gate_triggered",
        }

    return action


def run(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    in_path = ROOT / cfg["output"]["sample_data_dir"] / "sample_semantic_inputs.jsonl"
    if not in_path.exists():
        raise FileNotFoundError(f"Missing {in_path}. Run generate_semantic_inputs.py first.")
    inputs = read_jsonl(in_path)
    outputs = []
    for i, desc in enumerate(inputs):
        action = decide_action(desc, cfg)
        action["record_id"] = i
        action["client_id"] = desc["client_id"]
        outputs.append(action)
    out_dir = ensure_dir(cfg["output"]["sample_data_dir"])
    out_path = out_dir / "sample_irs_outputs.jsonl"
    write_jsonl(out_path, outputs)
    print(f"Wrote {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default_simulation.yaml")
    args = parser.parse_args()
    run(args.config)
