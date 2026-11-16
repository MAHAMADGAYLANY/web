import argparse
import json
from pathlib import Path

from privacy_pipeline import duckdb_summary, ml_utility_report, private_total, protect_csv


def main():
    parser = argparse.ArgumentParser(description="Privacy-preserving big-data pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    protect = subparsers.add_parser("protect", help="Detect, mask, and encrypt PII in CSV batches")
    protect.add_argument("--input", type=Path, required=True)
    protect.add_argument("--output", type=Path, required=True)
    protect.add_argument("--key", type=Path, default=Path("outputs/pipeline.key"))
    protect.add_argument("--batch-size", type=int, default=1000)

    summary = subparsers.add_parser("summary", help="Run a DuckDB aggregate over protected CSV")
    summary.add_argument("--input", type=Path, required=True)

    utility = subparsers.add_parser("utility", help="Compare ML utility before and after protection")
    utility.add_argument("--input", type=Path, required=True)
    utility.add_argument("--protected", type=Path, required=True)

    dp = subparsers.add_parser("private-total", help="Calculate a differentially private total")
    dp.add_argument("--value", type=float, required=True)
    dp.add_argument("--epsilon", type=float, default=1.0)
    dp.add_argument("--sensitivity", type=float, default=1.0)

    args = parser.parse_args()
    if args.command == "protect":
        result = protect_csv(args.input, args.output, args.key, args.batch_size)
    elif args.command == "summary":
        result = duckdb_summary(args.input)
    elif args.command == "utility":
        result = ml_utility_report(args.input, args.protected)
    else:
        result = {"private_total": private_total(args.value, args.epsilon, args.sensitivity)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
