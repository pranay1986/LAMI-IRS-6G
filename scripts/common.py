"""Common utilities for the LAMI-IRS reproducibility package."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def dbm_to_mw(dbm: float) -> float:
    return 10 ** (dbm / 10.0)


def mw_to_dbm(mw: float) -> float:
    return 10.0 * math.log10(max(mw, 1e-30))


def db_to_linear(db: float) -> float:
    return 10 ** (db / 10.0)


def linear_to_db(x: float) -> float:
    return 10.0 * math.log10(max(x, 1e-30))


def phase_codebook(phase_bits: int) -> np.ndarray:
    levels = 2 ** int(phase_bits)
    return np.linspace(0.0, 2.0 * np.pi, levels, endpoint=False)


def path_loss_db(distance_m: float, reference_path_loss_db: float, exponent: float, reference_distance_m: float = 1.0) -> float:
    d = max(float(distance_m), reference_distance_m)
    return reference_path_loss_db + 10.0 * exponent * math.log10(d / reference_distance_m)


def rician_power_gain(rng: np.random.Generator, k_db: float, size: int | Tuple[int, ...] = 1) -> np.ndarray:
    """Generate normalized Rician power gain samples."""
    k = db_to_linear(k_db)
    los = math.sqrt(k / (k + 1.0))
    sigma = math.sqrt(1.0 / (2.0 * (k + 1.0)))
    h = los + sigma * (rng.normal(size=size) + 1j * rng.normal(size=size))
    return np.abs(h) ** 2


def rayleigh_power_gain(rng: np.random.Generator, size: int | Tuple[int, ...] = 1) -> np.ndarray:
    h = (rng.normal(size=size) + 1j * rng.normal(size=size)) / math.sqrt(2.0)
    return np.abs(h) ** 2


def compute_snr_db(
    tx_power_dbm: float,
    noise_floor_dbm: float,
    distance_m: float,
    reference_path_loss_db: float,
    path_loss_exponent: float,
    fading_power: float,
    irs_gain_db: float = 0.0,
    interference_db: float = 0.0,
) -> float:
    pl = path_loss_db(distance_m, reference_path_loss_db, path_loss_exponent)
    rx_power_dbm = tx_power_dbm - pl + linear_to_db(fading_power) + irs_gain_db
    # Model interference as an additive degradation in dB for compact reconstruction.
    return rx_power_dbm - noise_floor_dbm - interference_db


def write_jsonl(path: str | Path, records: Iterable[Dict[str, Any]]) -> None:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True) + "\n")


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    out: List[Dict[str, Any]] = []
    if not p.exists():
        return out
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def confidence_interval(values: np.ndarray, confidence: float = 0.95) -> Tuple[float, float, float]:
    vals = np.asarray(values, dtype=float)
    mean = float(np.mean(vals))
    if vals.size <= 1:
        return mean, mean, mean
    se = float(np.std(vals, ddof=1) / math.sqrt(vals.size))
    # Normal approximation. Fine for the reconstruction package; default trials=100.
    z = 1.96 if abs(confidence - 0.95) < 1e-6 else 1.96
    return mean, mean - z * se, mean + z * se


def save_csv(df: pd.DataFrame, path: str | Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    ensure_dir(p.parent)
    df.to_csv(p, index=False)
    return p
