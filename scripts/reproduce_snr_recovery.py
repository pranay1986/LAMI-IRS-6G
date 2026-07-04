"""Reconstruct temporal SNR recovery under induced faults/interference."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import confidence_interval, ensure_dir, load_yaml, save_csv


def simulate_scheme(rng: np.random.Generator, scheme: str, time_ms: np.ndarray, trial: int) -> np.ndarray:
    base = 18.0 + rng.normal(0.0, 0.25)
    snr = base + 0.25 * np.sin(time_ms / 90.0)
    fault_times = [150, 350, 550, 750]
    params = {
        "Conventional IRS": {"drop": 7.0, "recovery": 160.0, "noise": 0.75, "gain": -1.0},
        "DRL-based IRS": {"drop": 4.4, "recovery": 90.0, "noise": 0.45, "gain": 0.5},
        "Standalone LLM-IRS": {"drop": 3.7, "recovery": 70.0, "noise": 0.38, "gain": 1.0},
        "LAMI": {"drop": 2.3, "recovery": 35.0, "noise": 0.22, "gain": 2.1},
    }[scheme]
    snr = snr + params["gain"]
    for ft in fault_times:
        decay = np.exp(-np.maximum(time_ms - ft, 0) / params["recovery"])
        active = (time_ms >= ft) & (time_ms <= ft + 180)
        snr[active] -= params["drop"] * decay[active]
    snr += rng.normal(0.0, params["noise"], size=time_ms.size)
    return snr


def run(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    rng = np.random.default_rng(cfg.get("seed", 42) + 11)
    trials = int(cfg["channel"]["trials"])
    time_ms = np.arange(0, 1000 + 1, 10)
    schemes = ["Conventional IRS", "DRL-based IRS", "Standalone LLM-IRS", "LAMI"]
    rows = []
    for scheme in schemes:
        all_trials = []
        for trial in range(trials):
            all_trials.append(simulate_scheme(rng, scheme, time_ms, trial))
        arr = np.vstack(all_trials)
        for i, t in enumerate(time_ms):
            mean, lo, hi = confidence_interval(arr[:, i])
            rows.append({"scheme": scheme, "time_ms": int(t), "snr_db_mean": mean, "snr_db_ci_low": lo, "snr_db_ci_high": hi})
    df = pd.DataFrame(rows)
    out_dir = ensure_dir(cfg["output"]["results_dir"])
    out_path = out_dir / "snr_recovery_results.csv"
    save_csv(df, out_path)

    fig_dir = ensure_dir(cfg["output"]["figures_dir"])
    plt.figure(figsize=(8, 4.5))
    for scheme in schemes:
        s = df[df["scheme"] == scheme]
        plt.plot(s["time_ms"], s["snr_db_mean"], label=scheme)
        plt.fill_between(s["time_ms"].to_numpy(), s["snr_db_ci_low"].to_numpy(), s["snr_db_ci_high"].to_numpy(), alpha=0.15)
    plt.xlabel("Time (ms)")
    plt.ylabel("SNR (dB)")
    plt.title("Temporal SNR recovery under induced faults")
    plt.legend()
    plt.tight_layout()
    fig_path = fig_dir / "snr_recovery.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Wrote {out_path}")
    print(f"Wrote {fig_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default_simulation.yaml")
    args = parser.parse_args()
    run(args.config)
