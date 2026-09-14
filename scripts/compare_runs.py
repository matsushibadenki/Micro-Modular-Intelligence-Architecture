"""Compare two immutable MMIA prediction logs using paired semantic groups."""

import argparse
import json
from pathlib import Path

from mmia.analysis import paired_group_difference
from mmia.harness import file_hash, write_json


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    baseline, candidate = read(args.baseline), read(args.candidate)
    report = {"baseline_sha256": file_hash(args.baseline),
              "candidate_sha256": file_hash(args.candidate),
              "strict_metric": True,
              "all": paired_group_difference(baseline, candidate)}
    for field in ("domain", "language", "difficulty"):
        for value in sorted({row[field] for row in baseline}):
            left = [row for row in baseline if row[field] == value]
            right = [row for row in candidate if row[field] == value]
            report[f"{field}/{value}"] = paired_group_difference(left, right)
    write_json(output, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
