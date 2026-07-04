"""Estimate controller-side scalability for larger IRS sizes and user densities."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import ensure_dir, load_yaml, save_csv


def run(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    irs_sizes = cfg["irs_sizes"]
    user_counts = cfg["user_counts"]
    region_size = int(cfg["region_size"])
    rows = []
    for n in irs_sizes:
        regions = int(np.ceil(n / region_size))
        for u in user_counts:
            validation_latency = cfg["base_validation_latency_ms_for_64"] * (n / 64.0)
            fusion_latency = cfg["base_fusion_latency_ms_for_25_users"] * (u / 25.0)
            # LLM is assumed to operate on compact descriptors and region summaries;
            # therefore its growth is logarithmic/mild rather than proportional to N.
            llm_latency = cfg["base_llm_latency_ms"] * (1.0 + 0.08 * np.log2(n / 64.0))
            sync_overhead = 0.01 * regions + 0.001 * u
            total_latency = 0.21 + 0.05 + fusion_latency + llm_latency + validation_latency + sync_overhead
            memory_mb = cfg["base_memory_mb"] + (n * cfg["per_element_control_bytes"] + cfg["memory_window"] * cfg["per_memory_record_bytes"] * u) / (1024 ** 2)
            rows.append({
                "irs_elements": n,
                "regions": regions,
                "user_count": u,
                "estimated_latency_ms": total_latency,
                "estimated_memory_mb": memory_mb,
                "validation_latency_ms": validation_latency,
                "fusion_latency_ms": fusion_latency,
                "llm_latency_ms": llm_latency,
                "sync_overhead_ms": sync_overhead,
            })
    df = pd.DataFrame(rows)
    out_dir = ensure_dir(cfg["results_dir"])
    out_path = out_dir / "scalability_results.csv"
    save_csv(df, out_path)

    fig_dir = ensure_dir(cfg["figures_dir"])
    for metric, fname, ylabel in [
        ("estimated_latency_ms", "scalability_latency.png", "Estimated controller-side latency (ms)"),
        ("estimated_memory_mb", "scalability_memory.png", "Estimated memory footprint (MB)"),
    ]:
        plt.figure(figsize=(8, 4.5))
        for u in user_counts:
            s = df[df["user_count"] == u]
            plt.plot(s["irs_elements"], s[metric], marker="o", label=f"U={u}")
        plt.xlabel("IRS elements")
        plt.ylabel(ylabel)
        plt.title(f"Scalability reconstruction: {ylabel}")
        plt.legend()
        plt.tight_layout()
        fig_path = fig_dir / fname
        plt.savefig(fig_path, dpi=300)
        plt.close()
        print(f"Wrote {fig_path}")
    print(f"Wrote {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/irs_scalability.yaml")
    args = parser.parse_args()
    run(args.config)
