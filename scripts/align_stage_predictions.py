"""Align stage-view predictions to immutable source example ids."""

import argparse
import json
from pathlib import Path

from mmia.harness import canonical, file_hash, write_json


def align(records):
    aligned, seen = [], set()
    for record in records:
        source_id = record.get("source_id")
        if not source_id or source_id in seen:
            raise ValueError("Missing or duplicate source_id")
        seen.add(source_id)
        aligned.append({**record, "stage_view_id": record["id"], "id": source_id})
    return aligned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source, output = Path(args.input), Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    records = align([json.loads(line) for line in source.read_text().splitlines()])
    with output.open("x") as stream:
        stream.write("".join(canonical(row) + "\n" for row in records))
    write_json(output.with_suffix(".manifest.json"), {
        "status": "completed", "source_sha256": file_hash(source),
        "output_sha256": file_hash(output), "rows": len(records),
        "transformation": "id=source_id; original stage id retained as stage_view_id"})


if __name__ == "__main__":
    main()
