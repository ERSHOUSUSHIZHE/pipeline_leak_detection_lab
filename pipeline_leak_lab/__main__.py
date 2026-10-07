from __future__ import annotations

import argparse
from pathlib import Path

from .detector import run_analysis
from .simulator import generate_windows, write_windows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic pipeline signals and evaluate a leak-event baseline.")
    parser.add_argument("--output-dir", default="reports", help="Directory for synthetic input and result files")
    parser.add_argument("--windows", type=int, default=1200, help="Number of synthetic signal windows")
    parser.add_argument("--seed", type=int, default=17, help="Random seed for reproducible data")
    args = parser.parse_args()

    output = Path(args.output_dir)
    samples = output / "synthetic_windows.csv"
    write_windows(samples, generate_windows(args.windows, args.seed))
    metrics = run_analysis(samples, output)
    print(f"Generated {metrics['synthetic_windows']} synthetic signal windows.")
    print(f"Candidate alarm windows: {metrics['candidate_alarm_windows']}")
    print(
        "Synthetic-only precision/recall/F1: "
        f"{metrics['precision_synthetic_only']:.3f} / "
        f"{metrics['recall_synthetic_only']:.3f} / "
        f"{metrics['f1_synthetic_only']:.3f}"
    )
    print(f"Reports written to {output.resolve()}")


if __name__ == "__main__":
    main()
