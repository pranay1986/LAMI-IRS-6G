"""Reconstruct latency and energy comparison for IRS control schemes."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from common import ensure_dir, load_yaml, save_csv


def run(config_path: str) -> Path:
    cfg = load_yaml(config_path)
    rows = []
    for name, s in cfg["schemes"].items():
        rows.append({
            "scheme": name,
            "reasoning_type": s["reasoning_type"],
            "energy_mj": float(s["energy_mj"]),
            "latency_ms": float(s["latency_ms"]),
            "notes": s["notes"],
        })
    df = pd.DataFrame(rows)
    standalone = df.loc[df["scheme"] == "Standalone LLM-IRS"].iloc[0]
    lami = df.loc[df["scheme"] == "LAMI"].iloc[0]
    energy_reduction = 100.0 * (standalone["energy_mj"] - lami["energy_mj"]) / standalone["energy_mj"]
    latency_reduction = 100.0 * (standalone["latency_ms"] - lami["latency_ms"]) / standalone["latency_ms"]
    df["energy_reduction_vs_standalone_llm_percent"] = energy_reduction
    df["latency_reduction_vs_standalone_llm_percent"] = latency_reduction

    out_dir = ensure_dir(cfg["results_dir"])
    out_path = out_dir / "latency_energy_results.csv"
    save_csv(df, out_path)

    fig_dir = ensure_dir(cfg["figures_dir"])
    ax = df.plot(x="scheme", y=["energy_mj", "latency_ms"], kind="bar", figsize=(9, 4), secondary_y="latency_ms")
    ax.set_ylabel("Energy per decision (mJ)")
    ax.right_ax.set_ylabel("Latency (ms)")
    ax.set_xlabel("")
    ax.set_title("Energy and latency reconstruction")
    plt.tight_layout()
    fig_path = fig_dir / "latency_energy_comparison.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Wrote {out_path}")
    print(f"Wrote {fig_path}")
    print(f"LAMI vs standalone LLM: energy reduction={energy_reduction:.1f}%, latency reduction={latency_reduction:.1f}%")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/latency_energy_accounting.yaml")
    args = parser.parse_args()
    run(args.config)
