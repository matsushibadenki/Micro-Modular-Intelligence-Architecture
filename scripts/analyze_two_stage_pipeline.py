"""Analyze correctness propagation and end-to-end latency of a two-stage run."""

import argparse
import json
from pathlib import Path

from mmia.harness import file_hash, percentile, write_json


def analyze(stage1, stage2):
    upstream = {row["source_id"]: row for row in stage1}
    downstream = {row["id"]: row for row in stage2}
    if upstream.keys() != downstream.keys():
        raise ValueError("Stage predictions must cover identical source ids")
    pairs = [(upstream[key], downstream[key]) for key in sorted(upstream)]
    total_times = [a["completion_seconds"] + b["completion_seconds"] for a, b in pairs
                   if a["completion_seconds"] is not None and b["completion_seconds"] is not None]
    upstream_correct = sum(a["correct"] for a, _ in pairs)
    final_correct = sum(b["correct"] for _, b in pairs)
    both_correct = sum(a["correct"] and b["correct"] for a, b in pairs)
    recovered = sum(not a["correct"] and b["correct"] for a, b in pairs)
    lost_after_correct = sum(a["correct"] and not b["correct"] for a, b in pairs)
    return {"rows": len(pairs), "stage1_correct": upstream_correct,
            "stage1_accuracy": upstream_correct / len(pairs),
            "pipeline_final_correct": final_correct,
            "pipeline_final_accuracy": final_correct / len(pairs),
            "both_stages_correct": both_correct,
            "final_correct_despite_wrong_intermediate": recovered,
            "final_wrong_despite_correct_intermediate": lost_after_correct,
            "end_to_end_completion_p50_seconds": percentile(total_times, .5),
            "end_to_end_completion_p95_seconds": percentile(total_times, .95),
            "latency_rows": len(total_times)}


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage1", required=True)
    parser.add_argument("--stage2", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = analyze(read(args.stage1), read(args.stage2))
    report["stage1_sha256"] = file_hash(args.stage1)
    report["stage2_sha256"] = file_hash(args.stage2)
    write_json(args.output, report)


if __name__ == "__main__":
    main()
