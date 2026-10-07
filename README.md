# Pipeline Leak Detection Lab

An independent learning project that explores a small part of a fiber-optic pipeline monitoring workflow: converting sensor-like signal windows into candidate leak alarms.

The demo generates synthetic windows for normal operation, a leak-like acoustic event, and third-party interference. It extracts RMS amplitude and high-frequency energy from each waveform, combines them with simulated temperature and pressure changes, then evaluates a rule-based detector.

## Run

From this directory, using Python 3.10 or newer:

```bash
python -m pipeline_leak_lab --output-dir reports --windows 1200 --seed 17
python -m unittest discover -s tests -v
```

The command writes:

- `reports/synthetic_windows.csv` — labeled, simulated waveforms and supporting sensor values
- `reports/leak_alarms.csv` — candidate leak windows, with timestamps, route positions, scores, and extracted features
- `reports/evaluation.json` — confusion counts and precision, recall, and F1 on the generated dataset

## Prototype design

- Simulates 64-sample signal windows at normal operation, leak-like high-frequency activity, and lower-frequency third-party interference.
- Extracts RMS amplitude and a high-frequency energy ratio with a discrete Fourier transform implemented using Python's standard library.
- Combines signal features with simulated temperature and pressure changes to score candidate leak windows.
- Reports each candidate's synthetic timestamp and route position, plus basic classification metrics.

## Scope and limitations

This is a self-directed educational prototype, not a company project or field deployment. Every waveform, label, temperature change, pressure change, and route location is synthetic. The model is a transparent rule-based baseline; it is not trained or validated on real pipeline or interrogator data, and its metrics do not represent expected field performance. It does not connect to fiber-optic interrogator hardware, SCADA, or operational alarm systems.

The project is intended to demonstrate a reproducible signal-processing workflow and a way to reason about event detection. A real monitoring system would require domain-reviewed sensor data, calibration, event-level validation, robust handling of operating conditions, and safety engineering.
