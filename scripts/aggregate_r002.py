"""Aggregate paired R002 comparisons across registered training seeds."""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from mmia.harness import file_hash, write_json


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def percentile_interval(estimates):
    values = sorted(estimates)
    n = len(values)
    return values[int(n * .025)], values[min(n - 1, int(n * .975))]


def aggregate(pairs, seed=20260917, samples=20000):
    if len(pairs) < 2 or samples < 2:
        raise ValueError("Need at least two seed pairs and bootstrap samples")
    per_seed, group_seed_deltas = [], defaultdict(list)
    expected_ids = None
    hashes = []
    for label, baseline_path, candidate_path in pairs:
        baseline, candidate = read(baseline_path), read(candidate_path)
        left, right = {r["id"]: r for r in baseline}, {r["id"]: r for r in candidate}
        if left.keys() != right.keys() or (expected_ids is not None and left.keys() != expected_ids):
            raise ValueError("Every seed must contain identical paired example ids")
        expected_ids = left.keys()
        grouped = defaultdict(list)
        for example_id in left:
            group_id = left[example_id]["group_id"]
            if group_id != right[example_id]["group_id"]:
                raise ValueError("Semantic group mismatch")
            grouped[group_id].append(int(right[example_id]["correct"]) - int(left[example_id]["correct"]))
        deltas = {group: sum(values) / len(values) for group, values in grouped.items()}
        for group, value in deltas.items():
            group_seed_deltas[group].append(value)
        per_seed.append({"seed": label,
                         "mixed_accuracy": sum(r["correct"] for r in baseline) / len(baseline),
                         "specialist_accuracy": sum(r["correct"] for r in candidate) / len(candidate),
                         "difference": sum(deltas.values()) / len(deltas)})
        hashes.append({"seed": label, "baseline_sha256": file_hash(baseline_path),
                       "candidate_sha256": file_hash(candidate_path)})
    if any(len(values) != len(pairs) for values in group_seed_deltas.values()):
        raise ValueError("Semantic groups differ across seeds")
    group_means = [sum(values) / len(values) for values in group_seed_deltas.values()]
    estimate = sum(group_means) / len(group_means)
    rng = random.Random(seed)
    cluster = [sum(rng.choice(group_means) for _ in group_means) / len(group_means)
               for _ in range(samples)]
    cluster_ci = percentile_interval(cluster)
    matrix = list(group_seed_deltas.values())
    hierarchical = []
    for _ in range(samples):
        seed_indices = [rng.randrange(len(pairs)) for _ in pairs]
        chosen_groups = [rng.choice(matrix) for _ in matrix]
        hierarchical.append(sum(sum(group[i] for i in seed_indices) / len(seed_indices)
                                for group in chosen_groups) / len(chosen_groups))
    hierarchical_ci = percentile_interval(hierarchical)
    return {"seeds": per_seed, "prediction_hashes": hashes,
            "semantic_groups": len(group_means), "mean_candidate_minus_baseline": estimate,
            "primary_group_bootstrap": {"lower_95": cluster_ci[0], "upper_95": cluster_ci[1],
                                         "samples": samples, "seed": seed,
                                         "method": "bootstrap semantic groups after averaging seed deltas"},
            "sensitivity_hierarchical_bootstrap": {
                "lower_95": hierarchical_ci[0], "upper_95": hierarchical_ci[1],
                "samples": samples, "seed": seed,
                "method": "bootstrap training seeds and semantic groups"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", action="append", nargs=3,
                        metavar=("SEED", "MIXED", "SPECIALISTS"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    write_json(output, aggregate(args.pair))


if __name__ == "__main__":
    main()
