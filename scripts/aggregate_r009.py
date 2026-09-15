"""Aggregate registered MMIA-R009 baseline/pipeline seed pairs."""

import argparse
from pathlib import Path

from aggregate_r002 import aggregate
from mmia.harness import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", action="append", nargs=3,
                        metavar=("SEED", "BASELINE", "PIPELINE"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    report = aggregate(args.pair)
    report["seeds"] = [
        {"seed": row["seed"], "baseline_accuracy": row["mixed_accuracy"],
         "pipeline_accuracy": row["specialist_accuracy"],
         "difference": row["difference"]}
        for row in report["seeds"]
    ]
    write_json(output, report)


if __name__ == "__main__":
    main()
