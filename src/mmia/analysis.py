"""Cluster-aware analysis for multilingual MMIA prediction files."""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from .harness import canonical, file_hash, write_json


def group_metrics(records):
    groups = defaultdict(list)
    for row in records:
        groups[row["group_id"]].append(row)
    if not groups:
        raise ValueError("No prediction records")
    if any(len(rows) != 3 for rows in groups.values()):
        raise ValueError("Expected exactly three language rows per semantic group")
    scores = [sum(row["correct"] for row in rows) / len(rows) for rows in groups.values()]
    return {"semantic_groups": len(groups),
            "translation_macro_accuracy": sum(scores) / len(scores),
            "all_languages_correct_rate": sum(score == 1 for score in scores) / len(scores),
            "any_language_correct_rate": sum(score > 0 for score in scores) / len(scores)}


def cluster_bootstrap_interval(records, seed=20260913, samples=10000):
    """Percentile CI resampling semantic groups, retaining their translations."""
    groups = defaultdict(list)
    for row in records:
        groups[row["group_id"]].append(row)
    values = [sum(row["correct"] for row in rows) / len(rows) for rows in groups.values()]
    if not values or samples < 2:
        raise ValueError("Need semantic groups and at least two samples")
    rng = random.Random(seed)
    estimates = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(samples))
    return {"method": "semantic-group percentile bootstrap",
            "seed": seed, "samples": samples,
            "lower_95": estimates[int(samples * .025)],
            "upper_95": estimates[min(samples - 1, int(samples * .975))]}


def analyze(records):
    report = {"all": {**group_metrics(records), "accuracy_95_interval": cluster_bootstrap_interval(records)}}
    for field in ("domain", "difficulty"):
        for value in sorted({row[field] for row in records}):
            subset = [row for row in records if row[field] == value]
            report[f"{field}/{value}"] = {
                **group_metrics(subset), "accuracy_95_interval": cluster_bootstrap_interval(subset)}
    return report


def paired_group_difference(baseline, candidate, seed=20260914, samples=10000):
    """Candidate minus baseline, paired by example and clustered by semantic group."""
    left = {row["id"]: row for row in baseline}
    right = {row["id"]: row for row in candidate}
    if left.keys() != right.keys():
        raise ValueError("Paired runs must contain identical example ids")
    groups = defaultdict(list)
    for example_id in left:
        if left[example_id]["group_id"] != right[example_id]["group_id"]:
            raise ValueError("Semantic group mismatch")
        groups[left[example_id]["group_id"]].append(
            int(right[example_id]["correct"]) - int(left[example_id]["correct"]))
    values = [sum(deltas) / len(deltas) for deltas in groups.values()]
    rng = random.Random(seed)
    estimates = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(samples))
    return {"semantic_groups": len(values), "candidate_minus_baseline": sum(values) / len(values),
            "lower_95": estimates[int(samples * .025)],
            "upper_95": estimates[min(samples - 1, int(samples * .975))],
            "method": "paired semantic-group percentile bootstrap", "seed": seed, "samples": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source, output = Path(args.predictions), Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    records = [json.loads(line) for line in source.read_text().splitlines()]
    report = {"prediction_sha256": file_hash(source), "strict_primary_metric": True,
              "slices": analyze(records)}
    write_json(output, report)
    print(canonical(report))


if __name__ == "__main__":
    main()
