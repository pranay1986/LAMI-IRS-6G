"""Generate synthetic channel realizations aligned with the LAMI manuscript assumptions.

The script creates channel/SNR samples for a 6 GHz IRS-aided edge link with
Rician fading, path-loss exponent 2.4, 64 IRS elements by default, and
randomized IRS element failures in the 10-15% range.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, compute_snr_db, ensure_dir, load_yaml, rician_power_gain, save_csv


def generate(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    rng = np.random.default_rng(cfg.get("seed", 42))
    net = cfg["network"]
    irs = cfg["irs"]
    ch = cfg["channel"]
    interf = cfg["interference"]

    distances = list(range(net["distance_min_m"], net["distance_max_m"] + 1, net["distance_step_m"]))
    trials = int(ch["trials"])
    records = []
    for trial in range(trials):
        failure_rate = rng.uniform(irs["failure_rate_min"], irs["failure_rate_max"])
        active_fraction = 1.0 - failure_rate
        # Approximate coherent IRS gain grows with active elements, represented in dB.
        base_irs_gain_db = 10.0 * np.log10(max(1.0, irs["elements"] * active_fraction)) - 7.5
        for distance_m in distances:
            fading_power = float(rician_power_gain(rng, ch["rician_k_db"], size=1)[0])
            interference_db = float(interf["burst_db"] if rng.random() < 0.25 else rng.uniform(0.0, 1.5))
            snr_no_irs = compute_snr_db(
                net["transmit_power_dbm"],
                net["noise_floor_dbm"],
                distance_m,
                net["reference_path_loss_db"],
                net["path_loss_exponent"],
                fading_power,
                irs_gain_db=0.0,
                interference_db=interference_db,
            )
            snr_with_irs = compute_snr_db(
                net["transmit_power_dbm"],
                net["noise_floor_dbm"],
                distance_m,
                net["reference_path_loss_db"],
                net["path_loss_exponent"],
                fading_power,
                irs_gain_db=base_irs_gain_db,
                interference_db=interference_db,
            )
            records.append(
                {
                    "trial": trial,
                    "distance_m": distance_m,
                    "fading_power": fading_power,
                    "failure_rate": failure_rate,
                    "active_irs_fraction": active_fraction,
                    "interference_db": interference_db,
                    "snr_no_irs_db": snr_no_irs,
                    "snr_with_irs_db": snr_with_irs,
                }
            )
    out_dir = ensure_dir(cfg["output"]["sample_data_dir"])
    out_path = out_dir / "channel_realizations.csv"
    save_csv(pd.DataFrame(records), out_path)
    print(f"Wrote {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default_simulation.yaml")
    args = parser.parse_args()
    generate(args.config)
