"""Run the complete LAMI-IRS reference reconstruction workflow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    print("\n$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


if __name__ == "__main__":
    py = sys.executable
    run([py, "scripts/generate_channel_realizations.py", "--config", "configs/default_simulation.yaml"])
    run([py, "scripts/generate_semantic_inputs.py", "--config", "configs/default_simulation.yaml"])
    run([py, "scripts/lami_reference_controller.py", "--config", "configs/default_simulation.yaml"])
    run([py, "scripts/validate_irs_action.py", "--config", "configs/default_simulation.yaml"])
    run([py, "scripts/run_latency_energy_accounting.py", "--config", "configs/latency_energy_accounting.yaml"])
    run([py, "scripts/reproduce_snr_recovery.py", "--config", "configs/default_simulation.yaml"])
    run([py, "scripts/reproduce_distance_adaptation.py", "--config", "configs/default_simulation.yaml"])
    run([py, "scripts/reproduce_scalability_analysis.py", "--config", "configs/irs_scalability.yaml"])
    print("\nCompleted full LAMI-IRS reconstruction workflow.")
