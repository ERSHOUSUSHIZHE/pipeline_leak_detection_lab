from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


SAMPLE_COUNT = 64
SAMPLE_RATE_HZ = 1000
CLASSES = ("normal", "leak", "third_party_interference")


def _waveform(kind: str, rng: random.Random) -> list[float]:
    if kind == "leak":
        frequency_bin = 20
        amplitude = rng.uniform(0.85, 1.25)
        noise = 0.10
    elif kind == "third_party_interference":
        frequency_bin = 4
        amplitude = rng.uniform(1.7, 2.5)
        noise = 0.12
    else:
        frequency_bin = 2
        amplitude = rng.uniform(0.03, 0.15)
        noise = 0.12

    phase = rng.uniform(0, math.tau)
    return [
        amplitude * math.sin(math.tau * frequency_bin * i / SAMPLE_COUNT + phase)
        + rng.gauss(0, noise)
        for i in range(SAMPLE_COUNT)
    ]


def generate_windows(count: int = 1200, seed: int = 17) -> list[dict[str, str]]:
    """Create reproducible, explicitly synthetic signal windows."""
    if count < 1:
        raise ValueError("count must be at least 1")
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows: list[dict[str, str]] = []
    for index in range(count):
        kind = rng.choices(CLASSES, weights=(0.68, 0.16, 0.16), k=1)[0]
        if kind == "leak":
            temperature_delta = rng.uniform(0.25, 1.10)
            pressure_drop = rng.uniform(8.0, 25.0)
        elif kind == "third_party_interference":
            temperature_delta = rng.uniform(0.0, 0.08)
            pressure_drop = rng.uniform(0.0, 2.0)
        else:
            temperature_delta = rng.uniform(0.0, 0.05)
            pressure_drop = rng.uniform(0.0, 1.5)

        signal = _waveform(kind, rng)
        rows.append(
            {
                "window_id": f"W{index + 1:05d}",
                "timestamp_utc": (start + timedelta(seconds=index * 2)).isoformat(),
                "distance_m": str(rng.randrange(0, 5001, 25)),
                "event_label": kind,
                "temperature_delta_c": f"{temperature_delta:.4f}",
                "pressure_drop_kpa": f"{pressure_drop:.4f}",
                "signal_samples": ";".join(f"{value:.6f}" for value in signal),
            }
        )
    return rows


def write_windows(path: str | Path, rows: list[dict[str, str]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "window_id",
        "timestamp_utc",
        "distance_m",
        "event_label",
        "temperature_delta_c",
        "pressure_drop_kpa",
        "signal_samples",
    ]
    with target.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
