"""Generate SLM-style semantic descriptors from synthetic channel realizations."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, ensure_dir, load_yaml, write_jsonl


def _trend(current: float, previous: float | None) -> str:
    if previous is None:
        return "stable"
    if current < previous - 0.7:
        return "decreasing"
    if current > previous + 0.7:
        return "increasing"
    return "stable"


def generate(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    rng = np.random.default_rng(cfg.get("seed", 42) + 7)
    in_path = ROOT / cfg["output"]["sample_data_dir"] / "channel_realizations.csv"
    if not in_path.exists():
        raise FileNotFoundError(f"Missing {in_path}. Run generate_channel_realizations.py first.")
    df = pd.read_csv(in_path)
    region_count = int(cfg["irs"]["region_count"])
    semantic_records = []

    for trial, g in df.groupby("trial"):
        prev_snr = None
        for _, row in g.sort_values("distance_m").iterrows():
            snr = float(row["snr_with_irs_db"])
            interference = float(row["interference_db"])
            mobility_state = rng.choice(cfg["channel"]["mobility_levels"], p=[0.50, 0.35, 0.15]).item()
            priority_level = int(rng.choice([1, 2, 3, 4, 5], p=[0.20, 0.30, 0.25, 0.17, 0.08]))
            energy_state = float(np.clip(rng.normal(0.72, 0.12), 0.05, 1.0))

            coverage = float(np.clip((18.0 - snr) / 12.0, 0.0, 1.0))
            suppression = float(np.clip(interference / 6.0, 0.0, 1.0))
            saving = float(np.clip((energy_state - 0.55) + max(snr - 15.0, 0) / 20.0, 0.0, 1.0))
            confidence = float(np.clip(0.92 - 0.18 * (mobility_state == "high") - 0.10 * (interference > 4.0) + rng.normal(0, 0.035), 0.45, 0.98))

            rec = {
                "client_id": f"u_{int(trial) % cfg['network']['user_count']:03d}",
                "timestamp": float(row["distance_m"]),
                "measured_snr_db": round(snr, 3),
                "snr_trend": _trend(snr, prev_snr),
                "interference_db": round(interference, 3),
                "mobility_state": mobility_state,
                "energy_state": round(energy_state, 3),
                "priority_level": priority_level,
                "intent_scores": {
                    "coverage_recovery": round(coverage, 3),
                    "interference_suppression": round(suppression, 3),
                    "energy_saving": round(saving, 3),
                },
                "slm_confidence": round(confidence, 3),
                "region_hint": int(rng.integers(0, region_count)),
                "source": "synthetic_slm_descriptor",
            }
            semantic_records.append(rec)
            prev_snr = snr

    out_dir = ensure_dir(cfg["output"]["sample_data_dir"])
    out_path = out_dir / "sample_semantic_inputs.jsonl"
    write_jsonl(out_path, semantic_records)
    print(f"Wrote {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default_simulation.yaml")
    args = parser.parse_args()
    generate(args.config)
