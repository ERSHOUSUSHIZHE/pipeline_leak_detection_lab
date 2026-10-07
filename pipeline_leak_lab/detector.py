from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable


def parse_signal(value: str) -> list[float]:
    try:
        samples = [float(part) for part in value.split(";") if part]
    except ValueError as exc:
        raise ValueError("signal_samples must contain semicolon-separated numbers") from exc
    if len(samples) < 8:
        raise ValueError("signal window must contain at least 8 samples")
    return samples


def extract_features(samples: list[float]) -> dict[str, float]:
    """Return RMS and high-frequency energy ratio from a real-valued signal window."""
    count = len(samples)
    rms = math.sqrt(sum(sample * sample for sample in samples) / count)
    powers: list[float] = []
    for frequency_bin in range(1, count // 2 + 1):
        real = 0.0
        imaginary = 0.0
        for index, sample in enumerate(samples):
            angle = math.tau * frequency_bin * index / count
            real += sample * math.cos(angle)
            imaginary -= sample * math.sin(angle)
        powers.append(real * real + imaginary * imaginary)
    total_power = sum(powers)
    high_start = max(0, count // 4 - 1)
    high_power = sum(powers[high_start:])
    ratio = high_power / total_power if total_power else 0.0
    return {"rms": rms, "high_frequency_energy_ratio": ratio}


def score_window(features: dict[str, float], temperature_delta_c: float, pressure_drop_kpa: float) -> float:
    """Transparent heuristic score; this is not a calibrated probability."""
    rms_component = min(features["rms"] / 1.0, 1.0)
    hf_component = min(max(features["high_frequency_energy_ratio"], 0.0), 1.0)
    temperature_component = min(max(temperature_delta_c / 1.0, 0.0), 1.0)
    pressure_component = min(max(pressure_drop_kpa / 20.0, 0.0), 1.0)
    return (
        0.40 * rms_component
        + 0.35 * hf_component
        + 0.15 * temperature_component
        + 0.10 * pressure_component
    )


def is_candidate_leak(features: dict[str, float], temperature_delta_c: float, pressure_drop_kpa: float) -> tuple[bool, float]:
    score = score_window(features, temperature_delta_c, pressure_drop_kpa)
    confirmed_channel = temperature_delta_c >= 0.20 or pressure_drop_kpa >= 5.0
    detected = (
        score >= 0.60
        and features["high_frequency_energy_ratio"] >= 0.55
        and confirmed_channel
    )
    return detected, score


def analyze_rows(rows: Iterable[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    alarms: list[dict[str, object]] = []
    tp = fp = tn = fn = 0
    for row in rows:
        samples = parse_signal(row["signal_samples"])
        features = extract_features(samples)
        temp = float(row["temperature_delta_c"])
        pressure = float(row["pressure_drop_kpa"])
        detected, score = is_candidate_leak(features, temp, pressure)
        actual = row["event_label"] == "leak"
        if actual and detected:
            tp += 1
        elif actual and not detected:
            fn += 1
        elif not actual and detected:
            fp += 1
        else:
            tn += 1
        if detected:
            alarms.append(
                {
                    "window_id": row["window_id"],
                    "timestamp_utc": row["timestamp_utc"],
                    "distance_m": row["distance_m"],
                    "score": round(score, 4),
                    "rms": round(features["rms"], 4),
                    "high_frequency_energy_ratio": round(features["high_frequency_energy_ratio"], 4),
                    "temperature_delta_c": round(temp, 4),
                    "pressure_drop_kpa": round(pressure, 4),
                    "synthetic_label": row["event_label"],
                }
            )

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    metrics = {
        "synthetic_windows": tp + fp + tn + fn,
        "candidate_alarm_windows": len(alarms),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision_synthetic_only": round(precision, 4),
        "recall_synthetic_only": round(recall, 4),
        "f1_synthetic_only": round(f1, 4),
        "validation_note": "Metrics describe only this synthetic dataset and are not field performance estimates.",
    }
    return alarms, metrics


def run_analysis(input_csv: str | Path, output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with Path(input_csv).open("r", newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    alarms, metrics = analyze_rows(rows)
    alarm_path = output / "leak_alarms.csv"
    fields = [
        "window_id",
        "timestamp_utc",
        "distance_m",
        "score",
        "rms",
        "high_frequency_energy_ratio",
        "temperature_delta_c",
        "pressure_drop_kpa",
        "synthetic_label",
    ]
    with alarm_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(alarms)
    (output / "evaluation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
