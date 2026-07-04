"""Reconstruct distance-dependent SNR adaptation for prompting modes."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import compute_snr_db, confidence_interval, ensure_dir, load_yaml, rician_power_gain, save_csv


def run(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    rng = np.random.default_rng(cfg.get("seed", 42) + 19)
    net = cfg["network"]
    ch = cfg["channel"]
    irs = cfg["irs"]
    distances = np.arange(net["distance_min_m"], net["distance_max_m"] + 1, net["distance_step_m"])
    trials = int(ch["trials"])

    modes = {
        "Conventional IRS": {"gain_offset": 2.5, "distance_resilience": 0.00, "noise": 0.50},
        "Zero-shot LAMI": {"gain_offset": 5.0, "distance_resilience": 0.10, "noise": 0.36},
        "Few-shot LAMI": {"gain_offset": 5.8, "distance_resilience": 0.17, "noise": 0.30},
        "Structured-CoT LAMI": {"gain_offset": 6.5, "distance_resilience": 0.23, "noise": 0.26},
    }

    rows = []
    for mode, p in modes.items():
        for d in distances:
            vals = []
            for trial in range(trials):
                fading = float(rician_power_gain(rng, ch["rician_k_db"], size=1)[0])
                irs_gain = p["gain_offset"] + 10.0 * np.log10(np.sqrt(irs["elements"]))
                # Prompt-conditioned adaptation slightly compensates distance-related decay.
                irs_gain += p["distance_resilience"] * (d / 10.0)
                snr = compute_snr_db(
                    net["transmit_power_dbm"],
                    net["noise_floor_dbm"],
                    float(d),
                    net["reference_path_loss_db"],
                    net["path_loss_exponent"],
                    fading,
                    irs_gain_db=irs_gain,
                    interference_db=0.8,
                )
                snr += rng.normal(0.0, p["noise"])
                vals.append(snr)
            mean, lo, hi = confidence_interval(np.array(vals))
            rows.append({"mode": mode, "distance_m": int(d), "snr_db_mean": mean, "snr_db_ci_low": lo, "snr_db_ci_high": hi})
    df = pd.DataFrame(rows)
    out_dir = ensure_dir(cfg["output"]["results_dir"])
    out_path = out_dir / "distance_adaptation_results.csv"
    save_csv(df, out_path)

    fig_dir = ensure_dir(cfg["output"]["figures_dir"])
    plt.figure(figsize=(8, 4.5))
    for mode in modes:
        s = df[df["mode"] == mode]
        plt.plot(s["distance_m"], s["snr_db_mean"], label=mode)
        plt.fill_between(s["distance_m"].to_numpy(), s["snr_db_ci_low"].to_numpy(), s["snr_db_ci_high"].to_numpy(), alpha=0.15)
    plt.xlabel("Transmitter-receiver distance (m)")
    plt.ylabel("SNR (dB)")
    plt.title("Distance-dependent SNR adaptation")
    plt.legend()
    plt.tight_layout()
    fig_path = fig_dir / "distance_adaptation.png"
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
