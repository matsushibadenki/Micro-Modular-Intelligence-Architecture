"""Combine domain-specialist predictions after strict coverage checks."""

import argparse
import json
from pathlib import Path

from mmia.harness import DOMAINS, canonical, file_hash, summarize, write_json


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def combine(dataset_path, split, inputs):
    expected = {
        row["id"]: row for row in load_jsonl(dataset_path) if row["split"] == split
    }
    combined = {}
    source_hashes = {}
    for domain, path in inputs.items():
        records = load_jsonl(path)
        source_hashes[domain] = file_hash(path)
        if not records:
            raise ValueError(f"Empty specialist prediction file: {domain}")
        for record in records:
            if record["domain"] != domain:
                raise ValueError(f"{domain} specialist contains {record['domain']} row")
            if record["id"] in combined:
                raise ValueError(f"Duplicate prediction id: {record['id']}")
            if record["id"] not in expected:
                raise ValueError(f"Unexpected prediction id: {record['id']}")
            combined[record["id"]] = record
    missing = sorted(set(expected) - set(combined))
    if missing:
        raise ValueError(f"Missing {len(missing)} predictions; first={missing[0]}")
    return [combined[row_id] for row_id in sorted(combined)], source_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--output", required=True)
    parser.add_argument("--input", action="append", default=[], metavar="DOMAIN=PATH",
                        help="Repeat for arbitrary dataset domains")
    for domain in DOMAINS:
        parser.add_argument(f"--{domain}")
    args = parser.parse_args()
    inputs = {domain: getattr(args, domain) for domain in DOMAINS if getattr(args, domain)}
    for item in args.input:
        domain, separator, path = item.partition("=")
        if not separator or not domain or not path or domain in inputs:
            raise ValueError(f"Invalid or duplicate --input: {item}")
        inputs[domain] = path
    if not inputs:
        raise ValueError("At least one specialist input is required")
    records, hashes = combine(args.dataset, args.split, inputs)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "predictions.jsonl").open("x") as stream:
        stream.write("".join(canonical(record) + "\n" for record in records))
    write_json(output / "summary.json", summarize(records))
    write_json(output / "manifest.json", {
        "status": "completed", "routing": "oracle domain label",
        "dataset": args.dataset, "dataset_sha256": file_hash(args.dataset),
        "split": args.split, "example_count": len(records),
        "source_prediction_hashes": hashes,
        "output_prediction_sha256": file_hash(output / "predictions.jsonl"),
    })


if __name__ == "__main__":
    main()
